from __future__ import annotations

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from adapta.cli import app
from adapta.config import load_settings


REAL_LIVROS_DIR = Path(
    os.getenv("ADAPTA_PIPELINE_LIVROS_DIR", "/mnt/c/whatsweb/adapta-cli/livros")
)
RUN_REAL_TESTS = os.getenv("ADAPTA_RUN_REAL_PIPELINE_TESTS") == "1"


@pytest.mark.skipif(
    (not RUN_REAL_TESTS) or (not REAL_LIVROS_DIR.exists()),
    reason="Teste real do pipeline desabilitado ou pasta 'livros' ausente",
)
def test_pipeline_command_uses_real_livros_directory(tmp_path: Path) -> None:
    if not (os.getenv("ADAPTA_LOGIN") and os.getenv("ADAPTA_PASSWORD")):
        pytest.skip("Credenciais ADAPTA_LOGIN e ADAPTA_PASSWORD não disponíveis")

    load_settings()
    runner = CliRunner()
    output_dir = tmp_path / "saida"
    db_path = tmp_path / "pipeline.db"

    result = runner.invoke(
        app,
        [
            "pipeline",
            "--input-dir",
            str(REAL_LIVROS_DIR),
            "--output-dir",
            str(output_dir),
            "--db-path",
            str(db_path),
            "--log",
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert db_path.exists()
    assert any((output_dir / "indexes").glob("*.json"))
    assert any(output_dir.glob("docs_*/*.md")) or any(output_dir.glob("docs_*/*/*.md"))
