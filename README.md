# Kilo Workspace

> An AI-first, shareable dev workspace scaffold.

## What's Inside

| Layer | What it does |
|-------|-------------|
| `.devcontainer/` | VS Code / GitHub Codespaces dev container with Python, Node, Docker-in-Docker |
| `docker-compose.yml` | One-command dev environment (`docker compose up`) with optional Postgres |
| `scripts/` | Shell helpers: `setup.sh`, `dev.sh`, `lint.sh`, `test.sh` |
| `.github/workflows/` | CI pipeline + AI agent readiness checks |
| `examples/` | Starter projects (hello-world, API service) |

## Quick Start

### With Dev Container (recommended)

Open in VS Code with the Dev Containers extension, or use GitHub Codespaces. The container builds automatically and runs `scripts/setup.sh` on create.

### With Docker Compose

```bash
make dev              # Start dev container
make compose-with-db  # Start with Postgres
```

### Local

```bash
make setup    # Install deps (Python venv, node_modules)
make lint     # Run all linters
make test     # Run tests
make dev      # Start dev environment
```

## Scripts

- **`scripts/setup.sh`** — Idempotent environment setup (venv, npm, permissions)
- **`scripts/dev.sh`** — Start dev environment (Docker or local fallback)
- **`scripts/lint.sh`** — Run ShellCheck, Ruff, ESLint (whichever are available)
- **`scripts/test.sh`** — Run pytest and/or npm test

## Adding Your Own Code

Drop projects into the workspace root or into `examples/`. The scaffold is intentionally minimal — extend it:

- Add a `requirements-dev.txt` for Python dev deps
- Add a `package.json` for Node tooling
- Add more services to `docker-compose.yml`
- Add more workflows to `.github/workflows/`

## AI Agent Friendly

This workspace is designed for human + AI pair programming:

- Devcontainer gives agents a consistent environment
- Scripts are idempotent and safe to re-run
- CI validates agent-readiness on every PR
- No secrets committed — use `.env.example` as a template

## License

MIT
