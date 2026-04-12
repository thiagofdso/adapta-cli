from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _last_non_empty_line(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def test_prompt_command_writes_output_file(tmp_path: Path) -> None:
    output_file = tmp_path / "saida.txt"
    env = os.environ.copy()

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "adapta.cli",
            "prompt",
            "--model",
            "gpt",
            "--prompt",
            "quanto é 1+1 responda somente o valor",
            "--output",
            str(output_file),
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert _last_non_empty_line(result.stdout) == "2"
    assert _last_non_empty_line(output_file.read_text(encoding="utf-8")) == "2"
