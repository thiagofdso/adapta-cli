from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_models_command_lists_supported_models() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "adapta.cli",
            "models",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr

    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]

    assert lines
    assert "gpt\tGPT-5\tGPT_5" in lines
    assert "claude\tClaude 4.5 Sonnet\tCLAUDE_4_5_SONNET" in lines
