from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _create_venv(target: Path) -> Path:
    subprocess.run([sys.executable, "-m", "venv", str(target)], check=True)
    return target / "bin" / "python"


def test_local_install_script_exposes_command(tmp_path: Path) -> None:
    python_bin = _create_venv(tmp_path / "venv-local")
    install_home = tmp_path / "install-home"
    bin_home = tmp_path / "bin-home"
    env = os.environ.copy()
    env["PYTHON"] = str(python_bin)
    env["INSTALL_HOME"] = str(install_home)
    env["BIN_HOME"] = str(bin_home)

    subprocess.run(
        ["sh", "scripts/install-local.sh"], cwd=REPO_ROOT, env=env, check=True
    )

    result = subprocess.run(
        [str(bin_home / "adapta"), "--help"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Usage" in result.stdout


def test_remote_install_script_exposes_command(tmp_path: Path) -> None:
    python_bin = _create_venv(tmp_path / "venv-remote")
    install_home = tmp_path / "install-home"
    bin_home = tmp_path / "bin-home"
    env = os.environ.copy()
    env["PYTHON"] = str(python_bin)
    env["INSTALL_HOME"] = str(install_home)
    env["BIN_HOME"] = str(bin_home)

    repo_url = REPO_ROOT.as_uri()
    subprocess.run(
        ["sh", "scripts/install-remote.sh", repo_url],
        cwd=REPO_ROOT,
        env=env,
        check=True,
    )

    result = subprocess.run(
        [str(bin_home / "adapta"), "--help"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Usage" in result.stdout
