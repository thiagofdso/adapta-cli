from __future__ import annotations

import asyncio
from typing import TypeVar


T = TypeVar("T")


def run_async(awaitable):
    return asyncio.run(awaitable)
