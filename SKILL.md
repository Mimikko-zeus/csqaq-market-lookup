---
name: csqaq-market-lookup
description: Use when OpenClaw needs to discover, sync, and call CSQAQ market APIs from docs.csqaq.com, with sitemap-driven coverage of all documented endpoints.
---

# CSQAQ Market Lookup

## Overview

Use this skill in OpenClaw to call CSQAQ market APIs with full coverage of documented endpoints.
Do not maintain a static endpoint list by hand. Always sync from docs before broad usage.

## Quick Start

1. Get an API token from CSQAQ:
   - Open `https://csqaq.com/`
   - Sign in to your account
   - Find the API token management page in the account area
   - Copy your `ApiToken`

2. Set token in current shell:
```bash
$env:CSQAQ_API_TOKEN="<your_token>"
```

3. Sync docs into local references:
```bash
python scripts/csqaq_api.py sync
```

4. List available endpoints:
```bash
python scripts/csqaq_api.py list --limit 200
```

5. Call any endpoint by operation id:
```bash
python scripts/csqaq_api.py call --operation-id ______________api_v1_current_data_get --query type=init
```

If an `operationId` is not unique, add `--doc-id`:
```bash
python scripts/csqaq_api.py call --operation-id __good_____api_v1_info_good_get --doc-id 327138094
```

6. Call any endpoint by path + method:
```bash
python scripts/csqaq_api.py call --path /api/v1/current_data --method GET --query type=init
```

## OpenClaw Usage

1. Put this skill folder under OpenClaw skills directory:
```bash
mkdir -p ~/.openclaw/skills
git clone <your-repo-url> ~/.openclaw/skills/csqaq-market-lookup
```

2. Ensure Python dependency is available:
```bash
pip install pyyaml
```

3. Get token from `https://csqaq.com/`, then set API token in shell:
```bash
export CSQAQ_API_TOKEN="<your_token>"
```

4. Run initial sync and smoke test:
```bash
python ~/.openclaw/skills/csqaq-market-lookup/scripts/csqaq_api.py sync
python ~/.openclaw/skills/csqaq-market-lookup/scripts/csqaq_api.py call --path /api/v1/current_data --method GET --query type=init --pretty
```

5. In OpenClaw prompt, invoke this skill:
```text
Use $csqaq-market-lookup to sync CSQAQ docs, list endpoints, and call the endpoint I ask for.
```

## Workflow

1. Run `sync` first to pull all `api-*.md` documents from `https://docs.csqaq.com/sitemap.xml`.
2. Use `list` to find target endpoint metadata (`path`, `method`, `operationId`, tags, summary).
3. Use `call` with either `--operation-id` or `--path` + `--method`.
4. For write operations, pass body with `--json-body`, `--body-file`, or `--raw-body`.
5. If endpoint set changes, run `sync` again to refresh local coverage.

## Files

- `scripts/sync_csqaq_openapi.py`: Downloads all API docs and builds merged references.
- `scripts/csqaq_api.py`: Unified CLI (`sync`, `list`, `call`).
- `references/endpoints.json`: Structured endpoint catalog.
- `references/endpoints.md`: Human-readable endpoint list.
- `references/openapi-merged.json`: Merged OpenAPI document.
- `references/sync-report.json`: Sync metadata and diagnostics.

## Notes

- Default token source: `CSQAQ_API_TOKEN` environment variable.
- You can override token per call with `--api-token`.
- By default, requests target `https://api.csqaq.com`.
- Keep token out of committed files.
- Never hardcode real tokens in `SKILL.md`, scripts, or json files.
