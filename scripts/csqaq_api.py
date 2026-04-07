#!/usr/bin/env python3
"""Unified CSQAQ API CLI: sync docs, list endpoints, and call APIs."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from sync_csqaq_openapi import run_sync

DEFAULT_BASE_URL = "https://api.csqaq.com"
DEFAULT_REFERENCES_DIR = Path(__file__).resolve().parents[1] / "references"
DEFAULT_ENDPOINTS_FILE = DEFAULT_REFERENCES_DIR / "endpoints.json"


def parse_kv_list(pairs: list[str], label: str) -> list[tuple[str, str]]:
    parsed: list[tuple[str, str]] = []
    for raw in pairs:
        if "=" not in raw:
            raise ValueError(f"Invalid {label} '{raw}'. Expected key=value.")
        key, value = raw.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Invalid {label} '{raw}'. Key is empty.")
        parsed.append((key, value))
    return parsed


def load_endpoints(endpoints_file: Path) -> list[dict[str, Any]]:
    data = json.loads(endpoints_file.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Invalid endpoints file: {endpoints_file}")
    out: list[dict[str, Any]] = []
    for item in data:
        if isinstance(item, dict):
            out.append(item)
    return out


def resolve_endpoint(
    endpoints: list[dict[str, Any]],
    operation_id: str | None,
    doc_id: str | None,
    path: str | None,
    method: str | None,
) -> tuple[str, str, dict[str, Any] | None]:
    if path and method:
        normalized_path = path if path.startswith("/") else f"/{path}"
        normalized_method = method.upper()
        if endpoints:
            matches = [
                ep
                for ep in endpoints
                if str(ep.get("path", "")) == normalized_path
                and str(ep.get("method", "")).upper() == normalized_method
            ]
            if len(matches) == 1:
                return normalized_path, normalized_method, matches[0]
            if len(matches) > 1:
                raise ValueError(
                    f"Endpoint is ambiguous for {normalized_method} {normalized_path}. "
                    "Use --operation-id or --doc-id to disambiguate."
                )
        return normalized_path, normalized_method, None

    candidates = endpoints

    if operation_id:
        candidates = [ep for ep in candidates if str(ep.get("operationId", "")) == operation_id]
        if not candidates:
            raise ValueError(f"operationId not found: {operation_id}")

    if doc_id:
        target_doc_id = str(doc_id).removeprefix("api-")
        candidates = [ep for ep in candidates if str(ep.get("doc_id", "")) == target_doc_id]
        if not candidates:
            raise ValueError(f"doc_id not found in endpoint catalog: api-{target_doc_id}")

    if path:
        normalized_path = path if path.startswith("/") else f"/{path}"
        candidates = [ep for ep in candidates if str(ep.get("path", "")) == normalized_path]
        if not candidates:
            raise ValueError(f"path not found in endpoint catalog: {normalized_path}")

    if method:
        target_method = method.upper()
        candidates = [ep for ep in candidates if str(ep.get("method", "")).upper() == target_method]
        if not candidates:
            raise ValueError(f"method not found for selected endpoint candidates: {target_method}")

    if not candidates:
        raise ValueError("Unable to resolve endpoint. Provide --path + --method or --operation-id.")
    if len(candidates) > 1:
        preview = ", ".join(
            f"{ep.get('method')} {ep.get('path')} ({ep.get('operationId')})" for ep in candidates[:5]
        )
        raise ValueError(f"Endpoint is ambiguous. Refine filters. Candidates: {preview}")

    match = candidates[0]
    resolved_path = str(match.get("path", ""))
    resolved_method = str(match.get("method", "GET")).upper()
    if not resolved_path.startswith("/"):
        resolved_path = f"/{resolved_path}"
    return resolved_path, resolved_method, match


def build_url(base_url: str, path: str, query_pairs: list[tuple[str, str]]) -> str:
    path_fixed = path if path.startswith("/") else f"/{path}"
    url = f"{base_url.rstrip('/')}{path_fixed}"
    if query_pairs:
        url = f"{url}?{urllib.parse.urlencode(query_pairs, doseq=True)}"
    return url


def make_body_bytes(
    json_body: str | None,
    body_file: str | None,
    raw_body: str | None,
) -> tuple[bytes | None, str | None]:
    body_sources = [json_body is not None, body_file is not None, raw_body is not None]
    if sum(body_sources) > 1:
        raise ValueError("Only one body option is allowed: --json-body, --body-file, --raw-body")

    if json_body is not None:
        parsed = json.loads(json_body)
        return json.dumps(parsed, ensure_ascii=False).encode("utf-8"), "application/json"
    if body_file is not None:
        return Path(body_file).read_bytes(), None
    if raw_body is not None:
        return raw_body.encode("utf-8"), "text/plain; charset=utf-8"
    return None, None


def print_endpoints(endpoints: list[dict[str, Any]], limit: int) -> None:
    lines = []
    for ep in endpoints[:limit]:
        opid = ep.get("operationId", "")
        summary = ep.get("summary", "")
        line = (
            f"{ep.get('method', '').upper():<6} "
            f"{ep.get('path', ''):<34} "
            f"op={opid} doc=api-{ep.get('doc_id', '')}  {summary}"
        )
        lines.append(line)
    for line in lines:
        print(line)
    print(f"\nTotal matched endpoints: {len(endpoints)}")


def cmd_sync(args: argparse.Namespace) -> int:
    return run_sync(
        output_dir=Path(args.output_dir).resolve(),
        timeout=args.timeout,
        verbose=not args.quiet,
    )


def cmd_list(args: argparse.Namespace) -> int:
    endpoints_file = Path(args.endpoints_file).resolve()
    if not endpoints_file.exists():
        print(f"[ERROR] Endpoints file not found: {endpoints_file}")
        print("Run sync first: python scripts/csqaq_api.py sync")
        return 1

    endpoints = load_endpoints(endpoints_file)
    query = (args.filter or "").lower().strip()
    method = (args.method or "").upper().strip()

    filtered: list[dict[str, Any]] = []
    for ep in endpoints:
        if method and str(ep.get("method", "")).upper() != method:
            continue
        if query:
            haystack = " ".join(
                [
                    str(ep.get("path", "")),
                    str(ep.get("operationId", "")),
                    str(ep.get("summary", "")),
                    str(ep.get("doc_id", "")),
                    " ".join(str(tag) for tag in ep.get("tags", [])),
                ]
            ).lower()
            if query not in haystack:
                continue
        filtered.append(ep)

    if args.as_json:
        print(json.dumps(filtered[: args.limit], ensure_ascii=False, indent=2))
    else:
        print_endpoints(filtered, limit=args.limit)
    return 0


def cmd_call(args: argparse.Namespace) -> int:
    endpoints_file = Path(args.endpoints_file).resolve()
    endpoints: list[dict[str, Any]] = []

    needs_catalog = bool(args.operation_id or args.doc_id or args.path)
    if needs_catalog:
        if not endpoints_file.exists():
            # Path+method can still be called without local catalog, but token auto-detection is disabled.
            if args.path and args.method and not args.operation_id and not args.doc_id:
                endpoints = []
            else:
                print(f"[ERROR] Endpoints file not found: {endpoints_file}")
                print("Run sync first: python scripts/csqaq_api.py sync")
                return 1
        else:
            endpoints = load_endpoints(endpoints_file)
    elif endpoints_file.exists():
        # Optional lookup for better diagnostics.
        endpoints = load_endpoints(endpoints_file)

    try:
        path, resolved_method, matched_endpoint = resolve_endpoint(
            endpoints=endpoints,
            operation_id=args.operation_id,
            doc_id=args.doc_id,
            path=args.path,
            method=args.method,
        )
        query_pairs = parse_kv_list(args.query, "query")
        header_pairs = parse_kv_list(args.header, "header")
        body_bytes, implied_content_type = make_body_bytes(
            json_body=args.json_body,
            body_file=args.body_file,
            raw_body=args.raw_body,
        )
    except Exception as exc:  # noqa: BLE001 - user input validation path
        print(f"[ERROR] {exc}")
        return 1

    method = resolved_method
    if not args.method and body_bytes is not None and method == "GET":
        method = "POST"

    headers: dict[str, str] = {}
    for key, value in header_pairs:
        headers[key] = value

    token = args.api_token or os.getenv(args.token_env)
    has_token_header = any(key.lower() == "apitoken" for key in headers)
    if token and not has_token_header:
        headers["ApiToken"] = token
    endpoint_requires_token = bool(matched_endpoint and matched_endpoint.get("requires_api_token"))
    if (args.require_token or endpoint_requires_token) and "ApiToken" not in headers:
        print(
            "[ERROR] API token is required. "
            f"Get one from https://csqaq.com/ and set --api-token or export {args.token_env}."
        )
        return 1

    if body_bytes is not None:
        headers.setdefault("Content-Type", args.content_type or implied_content_type or "application/json")
    headers.setdefault("Accept", "application/json")

    url = build_url(args.base_url, path, query_pairs)
    request = urllib.request.Request(url=url, data=body_bytes, method=method, headers=headers)

    print(f"[CALL] {method} {url}")

    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as resp:
            status = resp.getcode()
            response_bytes = resp.read()
            content_type = resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        status = exc.code
        response_bytes = exc.read()
        content_type = exc.headers.get("Content-Type", "") if exc.headers else ""
    except urllib.error.URLError as exc:
        print(f"[ERROR] Request failed: {exc}")
        return 1

    body_text = response_bytes.decode("utf-8", errors="replace")
    print(f"[STATUS] {status}")

    if "application/json" in content_type.lower():
        try:
            parsed = json.loads(body_text)
            print(json.dumps(parsed, ensure_ascii=False, indent=2 if args.pretty else None))
        except json.JSONDecodeError:
            print(body_text)
    else:
        print(body_text)

    return 0 if 200 <= status < 300 else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CSQAQ API CLI for docs sync and endpoint calls.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="Sync all api-*.md docs and build references.")
    sync_parser.add_argument("--output-dir", default=str(DEFAULT_REFERENCES_DIR))
    sync_parser.add_argument("--timeout", type=float, default=30.0)
    sync_parser.add_argument("--quiet", action="store_true")
    sync_parser.set_defaults(func=cmd_sync)

    list_parser = subparsers.add_parser("list", help="List synced endpoints.")
    list_parser.add_argument("--endpoints-file", default=str(DEFAULT_ENDPOINTS_FILE))
    list_parser.add_argument("--filter", default="")
    list_parser.add_argument("--method", default="")
    list_parser.add_argument("--limit", type=int, default=100)
    list_parser.add_argument("--json", action="store_true", dest="as_json")
    list_parser.set_defaults(func=cmd_list)

    call_parser = subparsers.add_parser("call", help="Call an endpoint.")
    call_parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    call_parser.add_argument("--endpoints-file", default=str(DEFAULT_ENDPOINTS_FILE))

    call_parser.add_argument("--operation-id", default=None)
    call_parser.add_argument("--doc-id", default=None)
    call_parser.add_argument("--path", default=None)
    call_parser.add_argument("--method", default=None)

    call_parser.add_argument("--query", action="append", default=[])
    call_parser.add_argument("--header", action="append", default=[])

    call_parser.add_argument("--json-body", default=None)
    call_parser.add_argument("--body-file", default=None)
    call_parser.add_argument("--raw-body", default=None)
    call_parser.add_argument("--content-type", default="application/json")

    call_parser.add_argument("--api-token", default=None)
    call_parser.add_argument("--token-env", default="CSQAQ_API_TOKEN")
    call_parser.add_argument("--require-token", action="store_true")
    call_parser.add_argument("--timeout", type=float, default=30.0)
    call_parser.add_argument("--pretty", action="store_true")
    call_parser.set_defaults(func=cmd_call)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
