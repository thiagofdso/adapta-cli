# adapta-cli Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-12

## Active Technologies
- Python 3.11 + Typer, httpx, python-dotenv, pytest (001-build-adapta-cli)
- arquivos locais JSON e texto/markdown para configuração e saída; estado remoto efêmero de chat no serviço Adapta (001-build-adapta-cli)
- arquivos locais PDF, arquivos texto/markdown de saída, diretórios temporários locais e artefatos remotos efêmeros no serviço Adapta (001-build-adapta-cli)

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
- 001-build-adapta-cli: Added Python 3.11 + Typer, httpx, python-dotenv, pytest

- 001-build-adapta-cli: Added Python 3.11 + Typer, httpx, pydantic-settings, python-dotenv, pytest

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
