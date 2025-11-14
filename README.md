Status: Work in progress (WIP). Contributions are welcome while the tool surface and integration story stabilise.

# OpenProject MCP Server

A Model Context Protocol (MCP) server that gives AI assistants high-fidelity access to [OpenProject](https://www.openproject.org/) API v3. The server exposes curated tools for project discovery, work package collaboration, time tracking, attachments, wiki content, and user resolution—all through a fast asynchronous Python stack optimised for LLM workflows.

## Table of Contents
- [Overview](#overview)
- [Architecture at a Glance](#architecture-at-a-glance)
- [Tool Catalog](#tool-catalog)
- [Repository Layout](#repository-layout)
- [Quickstart](#quickstart)
- [Configuration](#configuration)
- [Running the Server](#running-the-server)
- [Working With MCP Clients](#working-with-mcp-clients)
- [Testing & Quality](#testing--quality)
- [Troubleshooting](#troubleshooting)
- [Known Limitations & Roadmap](#known-limitations--roadmap)
- [Contributing](#contributing)
- [License](#license)

## Overview
- **Purpose-built for MCP:** Ships with a `FastMCP` implementation that can be dropped into Claude Desktop, Cursor, modelcontextclient, or any other MCP host.
- **Async & resilient:** Uses `httpx` with request retries, exponential backoff, timeout tuning, and sanitised error handling.
- **Rich tool surface:** LLMs can comment on work packages, search across content, manage attachments, resolve users, log time, and query wiki pages.
- **Typed contracts:** Pydantic models validate every tool input to protect the OpenProject API from malformed prompts.
- **Pyproject-only tooling:** `uv` drives dependency management, ensuring reproducible environments and quick install times.

## Architecture at a Glance
| Layer | Purpose |
| --- | --- |
| `openproject_mcp.main` | Entry point that configures logging, loads settings, and boots the MCP server on stdio. |
| `openproject_mcp.server` | Creates the `FastMCP` instance, registers `system_ping`, and loads all domain-specific tool modules. |
| `openproject_mcp.config.Settings` | Pydantic settings model fed by `.env`/environment variables (URL, token, timeouts, pagination defaults). |
| `openproject_mcp.client.OpenProjectClient` | Async HTTP client with retry/backoff logic, uniform headers, and error mapping to domain exceptions. |
| `openproject_mcp.tools.*` | Tool implementations grouped by OpenProject domain (work packages, attachments, queries, time entries, users, wiki, projects). |
| `tests/` | Extensive async pytest suite covering positive flows, permission failures, validation errors, and stdio smoke tests. |

## Tool Catalog
Each tool is exposed via the MCP protocol—LLMs call them exactly as defined here.

### System
- `system_ping`: Quick readiness check (returns `{"ok": true}`) to let MCP clients validate connectivity.

### Work Packages (`src/openproject_mcp/tools/work_packages.py`)
- `add_comment`: Post Markdown comments with optional watcher notifications.
- `search_content`: Search work packages and/or projects, optionally capturing attachment matches.
- `append_work_package_description`: Append Markdown to an existing description while handling optimistic locking.
- `get_work_package_statuses`: List all statuses available to the authenticated user.
- `get_work_package_types`: List every type globally or scoped to a project.
- `resolve_status`: Turn a human status name into an ID/disambiguation payload.
- `resolve_type`: Resolve a type name inside a project, including fallback when the type exists but is disabled there.

### Attachments (`src/openproject_mcp/tools/attachments.py`)
- `attach_file_to_wp`: Upload local files to work packages via multipart/form-data.
- `list_attachments`: Enumerate attachments on a work package.
- `download_attachment`: Download binary content (optionally persisting to disk) with base64 responses for in-memory use.
- `get_attachment_content`: Fetch metadata plus a preview slice using HTTP range requests to save bandwidth.

### Projects (`src/openproject_mcp/tools/projects.py`)
- `get_project_memberships`: Fetch project member/role mappings with pagination and multi-page follow mode.
- `resolve_project`: Resolve names/identifiers with disambiguation hints so LLMs can pick the right project.

### Queries (`src/openproject_mcp/tools/queries.py`)
- `list_queries`: List saved queries (global or project-scoped).
- `run_query`: Execute saved queries and support prompt-time filter overrides.

### Time Entries (`src/openproject_mcp/tools/time_entries.py`)
- `list_time_entries`: Filter by project, work package, user, and date span using native OpenProject operators.
- `log_time`: Convert decimal hours to ISO-8601 durations and create time entries (including optional user, activity, and timestamps).

### Users (`src/openproject_mcp/tools/users.py`)
- `resolve_user`: Search active principals by name.
- `get_user_by_id`: Retrieve a single user with full metadata.

### Wiki (`src/openproject_mcp/tools/wiki.py`)
- `get_wiki_page`: Retrieve wiki metadata, versions, and cross-links.
- `attach_file_to_wiki`: Upload files to wiki pages.
- `list_wiki_page_attachments`: List attachments on a wiki page.

## Repository Layout
```
├── src/openproject_mcp
│   ├── main.py            # CLI entry point (stdio server)
│   ├── server.py          # FastMCP factory + tool registration
│   ├── config.py          # Pydantic settings (env-driven)
│   ├── client.py          # Resilient httpx/OpenProject client
│   ├── errors.py          # Domain-specific exceptions and sanitisation
│   ├── utils/logging.py   # Log configuration helper
│   └── tools/             # Tool families grouped by domain
├── tests/                 # Async pytest suite and smoke tests
├── pyproject.toml         # uv/PEP 621 metadata + tooling config
├── uv.lock                # Locked dependency graph
├── requirements.txt       # Convenience export (mirrors pyproject deps)
└── env_example.txt        # Template for `.env`
```

## Quickstart
1. **Install prerequisites**
   - Python 3.10+
   - [`uv`](https://docs.astral.sh/uv/) for blazing-fast installs (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
   - Access to an OpenProject instance and a personal API token
2. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/openproject-mcp-ai-integration.git
   cd openproject-mcp-ai-integration
   ```
3. **Install dependencies**
   ```bash
   uv sync  # creates .venv and installs runtime + dev deps
   ```
4. **Configure environment**
   ```bash
   cp env_example.txt .env
   # edit .env with your OpenProject URL + API token
   ```
5. **Run a smoke test**
   ```bash
   uv run python -m openproject_mcp.main  # prints nothing and blocks while serving stdio
   ```
   Stop with `Ctrl+C` once you confirm the server boots without configuration errors.

## Configuration
`openproject_mcp.config.Settings` consumes the following environment variables (case-insensitive thanks to Pydantic). Assign them in `.env` or via your MCP client configuration.

| Variable | Required | Description | Default |
| --- | --- | --- | --- |
| `OPENPROJECT_URL` / `OPENPROJECT_BASE_URL` | Yes | Base URL to your OpenProject instance (no `/api/v3`). | — |
| `OPENPROJECT_API_KEY` / `OPENPROJECT_API_TOKEN` | Yes | Personal API token with API v3 access. | — |
| `LOG_LEVEL` | Optional | Python logging level (`DEBUG`, `INFO`, …). | `INFO` |
| `CONNECT_TIMEOUT` | Optional | Seconds allowed to establish TCP/TLS connections. | `10.0` |
| `READ_TIMEOUT` | Optional | Seconds allowed for responses. | `10.0` |
| `MAX_RETRIES` | Optional | Retry attempts for retryable status codes/timeouts. | `3` |
| `PAGE_SIZE_DEFAULT` | Optional | Default pagination size for helper logic. | `25` |
| `PAGE_SIZE_MAX` | Optional | Hard ceiling for page sizes. | `200` |

Additional keys in `env_example.txt` (`OPENPROJECT_PROXY`, `TEST_CONNECTION_ON_STARTUP`) are placeholders for future enhancements and are currently ignored.

## Running the Server
The project exposes a console script named `openproj-mcp` (configured in `pyproject.toml`). Run it through `uv` to ensure dependencies are resolved via the project virtual environment:

```bash
uv run openproj-mcp
```

- The process blocks and communicates over stdio per MCP specification.
- Use `LOG_LEVEL=DEBUG` to surface HTTP requests/responses during debugging.
- Health-check via `system_ping` from your MCP client before invoking other tools.

## Working With MCP Clients
### Claude Desktop (macOS & Windows)
Add an entry to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "openproject": {
      "command": "uv",
      "args": ["run", "openproj-mcp"],
      "env": {
        "OPENPROJECT_URL": "https://your-instance.openproject.com",
        "OPENPROJECT_API_KEY": "sk_...",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

Restart Claude Desktop and confirm the server appears in the MCP tool list. Other MCP hosts (Cursor, Continue, etc.) follow the same pattern: point to `uv run openproj-mcp` and provide the environment through their configuration UI.

## Testing & Quality
The repo includes async-first tests plus static analysis hooks.

| Task | Command |
| --- | --- |
| Run entire test suite | `uv run pytest` |
| Focus on a specific test | `uv run pytest tests/test_work_packages.py -k add_comment` |
| Type checking | `uv run mypy src` |
| Linting | `uv run ruff check` |
| Formatting (check/fix) | `uv run black --check src tests` / `uv run black src tests` |
| Coverage report | `uv run pytest --cov=src/openproject_mcp --cov-report=term-missing` |

Helpful docs live in `tests/TESTING_CHECKLIST.md` (e.g., the checklist for `add_comment`).

## Troubleshooting
| Symptom | Likely Cause | Suggested Fix |
| --- | --- | --- |
| `AuthError: Authentication failed` | Invalid or revoked API token. | Regenerate the token under *My account → Access tokens* and update `.env`/client config. |
| `PermissionError: Permission denied` | The token lacks project/work package rights. | Grant the user the required OpenProject roles or run the operation in a project the user can access. |
| `404 Resource not found` | Wrong project/work package ID or the user cannot view it. | Double-check IDs via UI or `resolve_project`/`search_content`. |
| Stalled commands | Corporate proxies or SSL interception. | Run `curl` manually to confirm connectivity; proxy support is not yet wired, so a direct connection is required for now. |
| Slow responses | Large queries or wide attachment downloads. | Use filters (`pageSize`, `limit`, date ranges) or `get_attachment_content` for previews before downloading entire files. |

Set `LOG_LEVEL=DEBUG` to trace HTTP calls. The server mutes noisy `httpx` logs when running at higher log levels.

## Known Limitations & Roadmap
- Proxy configuration and startup connectivity tests are stubbed in `.env_example` but not implemented.
- Time entry activities must be referenced by ID (e.g., check OpenProject → *Administration → Time tracking*). A dedicated lookup tool is planned.
- There is no high-level permission inspection yet; use OpenProject’s UI to confirm rights if you receive 403 errors.
- Only stdio transport is provided today. Socket or HTTP transports would require additional glue around `FastMCP`.
- The tool surface focuses on read/write operations tested in `tests/`. If you need new API coverage (e.g., versions, relations), PRs are welcome.

## Contributing
1. Fork & clone the repo.
2. Create a feature branch: `git checkout -b feature/<topic>`.
3. Run `uv run ruff check`, `uv run black`, `uv run mypy`, and `uv run pytest` before committing.
4. Submit a PR describing the motivation, testing performed, and any OpenProject prerequisites.

Please avoid committing secrets—`.env` is gitignored, and `errors.py` scrubs sensitive tokens from exception text.

## Credits & Origins

This codebase was originally forked from the
[`openproject-mcp-server`](https://github.com/AndyEverything/openproject-mcp-server)
project by **AndyEverything** (MIT-licensed). Under Oleksandr Pometun's
maintenance it has since been heavily refactored into a distinct implementation
with a different architecture, tooling setup, and feature scope aimed at a
production-ready MCP server and portfolio reference.

## License
This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.

## Acknowledgements
- Inspired by the [Model Context Protocol](https://modelcontextprotocol.io/) community work.
- Integrates with [OpenProject API v3](https://docs.openproject.org/api/).
