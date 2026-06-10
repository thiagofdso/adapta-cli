# adapta-cli Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-14

## Active Technologies
- Python 3.11 + Typer, httpx, python-dotenv, pytest (001-build-adapta-cli)
- arquivos locais JSON e texto/markdown para configuração e saída; estado remoto efêmero de chat no serviço Adapta (001-build-adapta-cli)
- arquivos locais PDF, arquivos texto/markdown de saída, diretórios temporários locais e artefatos remotos efêmeros no serviço Adapta (001-build-adapta-cli)
- Python 3.11 + Typer, httpx, python-dotenv, pytest, biblioteca padrão `sqlite3` (001-build-adapta-cli)
- SQLite local para estado operacional do pipeline e filesystem para artefatos de saída (001-build-adapta-cli)
- Arquivos markdown e JSON no diretório do usuário; conversa remota efêmera no serviço Adapta (001-build-adapta-cli)

- Python 3.11 + Typer, httpx, pydantic-settings, python-dotenv, pytest (001-build-adapta-cli)

## Project Structure

```text
docs/
src/
tests/
```

## Commands

cd src && pytest && ruff check .

## Code Style

Python 3.11: Follow standard conventions

## Documentation Rules

- Consult `docs/features.md` and `docs/arquitetura.md` before changing behavior or structure
- Consult `docs/code-map.md` before editing existing modules
- Consult `docs/integracoes.md` before changing external service usage
- Consult `docs/licoes-aprendidas.md` and `docs/adr/` before technical decisions
- Update impacted files in `docs/` together with code changes
- Record relevant debugging mistakes and incidents in `docs/licoes-aprendidas.md`


## Recent Changes
- 001-build-adapta-cli: Added Python 3.11 + Typer, httpx, pydantic-settings, python-dotenv, pytest
- 001-build-adapta-cli: Added Python 3.11 + Typer, httpx, python-dotenv, pytest, biblioteca padrão `sqlite3`
- 001-build-adapta-cli: Added Python 3.11 + Typer, httpx, pydantic-settings, python-dotenv, pytest


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, invoke the `skill` tool with `skill: "graphify"` before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
