from __future__ import annotations

from pathlib import Path


def persist_output(text: str, output_path: Path | None) -> None:
    if output_path is None:
        return
    output_path.write_text(text, encoding="utf-8")
