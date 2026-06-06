from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _last_non_empty_line(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def test_prompt_file_command_reads_file(tmp_path: Path) -> None:
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("quanto é 1+1 responda somente o valor", encoding="utf-8")

    env = os.environ.copy()

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "adapta.cli",
            "prompt",
            "--model",
            "gpt",
            "--prompt-file",
            str(prompt_file),
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert _last_non_empty_line(result.stdout) == "2"
