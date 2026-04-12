from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_chat_command_runs_and_cleans_up() -> None:
    env = os.environ.copy()

    result = subprocess.run(
        [sys.executable, "-m", "adapta.cli", "chat", "--model", "gpt"],
        cwd=REPO_ROOT,
        env=env,
        input="quanto é 1+1 responda somente o valor\nexit\n",
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "2" in result.stdout
    assert "Falha ao limpar chat remoto" not in result.stderr


def test_chat_command_supports_interactive_model_selection() -> None:
    env = os.environ.copy()

    result = subprocess.run(
        [sys.executable, "-m", "adapta.cli", "chat"],
        cwd=REPO_ROOT,
        env=env,
        input="4\nquanto é 1+1 responda somente o valor\nexit\n",
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "2" in result.stdout
