#!/usr/bin/env python3
"""Sync CSQAQ API docs and build merged OpenAPI references."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install with: pip install pyyaml") from exc

DOCS_HOST = "https://docs.csqaq.com"
SITEMAP_URL = f"{DOCS_HOST}/sitemap.xml"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "references"
API_URL_RE = re.compile(r"^https://docs\.csqaq\.com/api-(\d+)$")
FENCED_YAML_RE = re.compile(r"```yaml\s*(.*?)\s*```", re.DOTALL)
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}
NON_ASCII_RE = re.compile(r"[^\x00-\x7F]+")


def fetch_text(url: str, timeout: float) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "csqaq-market-lookup/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def sanitize_ascii(text: str) -> str:
    cleaned = NON_ASCII_RE.sub(" ", text)
    cleaned = " ".join(cleaned.split())
    return cleaned.strip()


def sanitize_recursive(value: Any) -> Any:
    if isinstance(value, str):
        return sanitize_ascii(value)
    if isinstance(value, list):
        return [sanitize_recursive(item) for item in value]
    if isinstance(value, dict):
        return {key: sanitize_recursive(item) for key, item in value.items()}
    return value


def parse_api_doc_ids(sitemap_xml: str) -> list[str]:
    root = ET.fromstring(sitemap_xml)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    ids: list[str] = []
    for node in root.findall(".//sm:url/sm:loc", ns):
        if not node.text:
            continue
        loc = node.text.strip()
        match = API_URL_RE.match(loc)
        if match:
            ids.append(match.group(1))
    return ids


def extract_openapi_yaml(markdown_text: str) -> dict[str, Any]:
    match = FENCED_YAML_RE.search(markdown_text)
    if not match:
        raise ValueError("No fenced YAML block found.")
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict):
        raise ValueError("Parsed OpenAPI YAML is not an object.")
    return sanitize_recursive(data)


def parse_requires_api_token(operation: dict[str, Any]) -> bool:
    params = operation.get("parameters")
    if not isinstance(params, list):
        return False
    for param in params:
        if not isinstance(param, dict):
            continue
        if str(param.get("in", "")).lower() != "header":
            continue
        if str(param.get("name", "")).lower() == "apitoken":
            return bool(param.get("required", False))
    return False


def build_endpoint_items(
    doc_id: str,
    spec: dict[str, Any],
) -> list[dict[str, Any]]:
    paths = spec.get("paths")
    if not isinstance(paths, dict):
        return []

    items: list[dict[str, Any]] = []
    for path, path_item in paths.items():
        if not isinstance(path, str) or not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if str(method).lower() not in HTTP_METHODS:
                continue
            if not isinstance(operation, dict):
                continue
            raw_summary = str(operation.get("summary", ""))
            summary = sanitize_ascii(raw_summary)
            if not summary:
                summary = f"Endpoint from api-{doc_id}"

            raw_tags = operation.get("tags", [])
            tags: list[str] = []
            if isinstance(raw_tags, list):
                for tag in raw_tags:
                    tag_str = sanitize_ascii(str(tag))
                    if tag_str:
                        tags.append(tag_str)
            item = {
                "doc_id": doc_id,
                "doc_url": f"{DOCS_HOST}/api-{doc_id}",
                "doc_md_url": f"{DOCS_HOST}/api-{doc_id}.md",
                "path": path,
                "method": str(method).upper(),
                "operationId": operation.get("operationId", ""),
                "summary": summary,
                "deprecated": bool(operation.get("deprecated", False)),
                "tags": tags,
                "requires_api_token": parse_requires_api_token(operation),
            }
            items.append(item)
    return items


def merge_openapi_specs(specs: list[tuple[str, dict[str, Any]]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    merged: dict[str, Any] = {
        "openapi": "3.0.1",
        "info": {
            "title": "CSQAQ Data OpenAPI (Merged)",
            "version": "1.0.0",
            "description": "Merged from docs.csqaq.com/api-*.md pages.",
        },
        "servers": [{"url": "https://api.csqaq.com", "description": "Official environment"}],
        "paths": {},
        "components": {"schemas": {}, "securitySchemes": {}},
        "x-generated-at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }

    collisions: list[dict[str, Any]] = []
    merged_paths: dict[str, Any] = merged["paths"]
    merged_schemas: dict[str, Any] = merged["components"]["schemas"]
    merged_security: dict[str, Any] = merged["components"]["securitySchemes"]

    for doc_id, spec in specs:
        paths = spec.get("paths")
        if isinstance(paths, dict):
            for path, path_item in paths.items():
                if not isinstance(path, str) or not isinstance(path_item, dict):
                    continue
                target_path = merged_paths.setdefault(path, {})
                if not isinstance(target_path, dict):
                    continue
                for method, operation in path_item.items():
                    method_lower = str(method).lower()
                    if method_lower not in HTTP_METHODS or not isinstance(operation, dict):
                        continue
                    if method_lower in target_path:
                        collisions.append(
                            {
                                "doc_id": doc_id,
                                "path": path,
                                "method": method_lower,
                                "reason": "duplicate path+method",
                            }
                        )
                        continue
                    op = dict(operation)
                    op["x-source-doc"] = f"api-{doc_id}"
                    target_path[method_lower] = op

        components = spec.get("components")
        if not isinstance(components, dict):
            continue

        schemas = components.get("schemas")
        if isinstance(schemas, dict):
            for schema_name, schema_obj in schemas.items():
                if schema_name not in merged_schemas:
                    merged_schemas[schema_name] = schema_obj

        security_schemes = components.get("securitySchemes")
        if isinstance(security_schemes, dict):
            for key, value in security_schemes.items():
                if key not in merged_security:
                    merged_security[key] = value

    return merged, collisions


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def write_endpoints_markdown(path: Path, endpoints: list[dict[str, Any]]) -> None:
    lines = [
        "# CSQAQ Endpoints",
        "",
        "| Method | Path | Operation ID | Doc | Summary |",
        "|---|---|---|---|---|",
    ]
    for ep in endpoints:
        method = str(ep.get("method", ""))
        ep_path = str(ep.get("path", ""))
        operation_id = str(ep.get("operationId", ""))
        doc_id = str(ep.get("doc_id", ""))
        summary = str(ep.get("summary", "")).replace("|", "\\|")
        lines.append(
            f"| `{method}` | `{ep_path}` | `{operation_id}` | `api-{doc_id}` | {summary} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def run_sync(output_dir: Path, timeout: float, verbose: bool = True) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        sitemap_xml = fetch_text(SITEMAP_URL, timeout=timeout)
    except urllib.error.URLError as exc:
        print(f"[ERROR] Failed to fetch sitemap: {exc}")
        return 1

    doc_ids = parse_api_doc_ids(sitemap_xml)
    if not doc_ids:
        print("[ERROR] No API pages found in sitemap.")
        return 1

    specs: list[tuple[str, dict[str, Any]]] = []
    endpoints: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    for doc_id in doc_ids:
        md_url = f"{DOCS_HOST}/api-{doc_id}.md"
        try:
            markdown_text = fetch_text(md_url, timeout=timeout)
            spec = extract_openapi_yaml(markdown_text)
            specs.append((doc_id, spec))
            endpoints.extend(build_endpoint_items(doc_id, spec))
            if verbose:
                print(f"[OK] Synced api-{doc_id}")
        except Exception as exc:  # noqa: BLE001 - keep full failure details per document
            failures.append({"doc_id": doc_id, "md_url": md_url, "error": str(exc)})
            if verbose:
                print(f"[WARN] Failed api-{doc_id}: {exc}")

    merged_spec, collisions = merge_openapi_specs(specs)
    endpoints_sorted = sorted(
        endpoints,
        key=lambda ep: (
            str(ep.get("path", "")),
            str(ep.get("method", "")),
            str(ep.get("operationId", "")),
        ),
    )

    write_json(output_dir / "endpoints.json", endpoints_sorted)
    write_endpoints_markdown(output_dir / "endpoints.md", endpoints_sorted)
    write_json(output_dir / "openapi-merged.json", merged_spec)

    report = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": {"sitemap_url": SITEMAP_URL, "docs_host": DOCS_HOST},
        "counts": {
            "api_docs_discovered": len(doc_ids),
            "api_docs_synced": len(specs),
            "api_docs_failed": len(failures),
            "endpoints_extracted": len(endpoints_sorted),
            "collision_count": len(collisions),
        },
        "failures": failures,
        "collisions": collisions,
    }
    write_json(output_dir / "sync-report.json", report)

    if verbose:
        print(
            "[DONE] "
            f"docs={len(doc_ids)} synced={len(specs)} "
            f"failed={len(failures)} endpoints={len(endpoints_sorted)}"
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync CSQAQ OpenAPI docs into local references.")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Output directory for generated references (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="HTTP timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-document progress logs",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    return run_sync(output_dir=output_dir, timeout=args.timeout, verbose=not args.quiet)


if __name__ == "__main__":
    sys.exit(main())
