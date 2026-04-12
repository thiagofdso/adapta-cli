from __future__ import annotations

import os
from pathlib import Path
import shutil

import pytest
from typer.testing import CliRunner

from adapta.cli import app
from adapta.config import load_settings


REAL_PDF_PATH = Path(
    "/mnt/c/whatsweb/adapta-cli/Os_7_Habitos_das_Pessoas_Altamente_Eficazes-Stephen_Covey.pdf"
)
ROOT_OUTPUT_PATH = Path("/mnt/c/whatsweb/adapta-cli/saida.md")


@pytest.mark.skipif(
    not REAL_PDF_PATH.exists(), reason="PDF real não encontrado no workspace"
)
def test_destilador_command_uses_real_client(monkeypatch, tmp_path: Path) -> None:
    if not (os.getenv("ADAPTA_LOGIN") and os.getenv("ADAPTA_PASSWORD")):
        pytest.skip("Credenciais ADAPTA_LOGIN e ADAPTA_PASSWORD não disponíveis")

    # Garante cedo que a configuração real do ambiente está válida.
    load_settings()

    runner = CliRunner()
    output_path = tmp_path / "saida.md"

    result = runner.invoke(
        app,
        [
            "destilador",
            "--input",
            str(REAL_PDF_PATH),
            "--output",
            str(output_path),
            "--log",
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "# DIMENSÃO 1" in content
    assert "# DIMENSÃO 7" in content
    assert len(content.strip()) > 2000
    assert (
        "Processando Os_7_Habitos_das_Pessoas_Altamente_Eficazes-Stephen_Covey.pdf"
        in result.stdout
    )
    shutil.copy2(output_path, ROOT_OUTPUT_PATH)
