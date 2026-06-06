from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _base_env() -> dict[str, str]:
    return os.environ.copy()


def _last_non_empty_line(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def test_prompt_command_returns_expected_answer() -> None:
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
        ],
        cwd=REPO_ROOT,
        env=_base_env(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert _last_non_empty_line(result.stdout) == "2"


def test_prompt_command_uses_default_model_from_environment() -> None:
    env = _base_env()
    env["ADAPTA_MODEL"] = "gpt"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "adapta.cli",
            "prompt",
            "--prompt",
            "quanto é 1+1 responda somente o valor",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert _last_non_empty_line(result.stdout) == "2"


def test_prompt_command_supports_interactive_model_selection() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "adapta.cli",
            "prompt",
            "--prompt",
            "quanto é 1+1 responda somente o valor",
        ],
        cwd=REPO_ROOT,
        env=_base_env(),
        input="4\n",
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert _last_non_empty_line(result.stdout) == "2"
