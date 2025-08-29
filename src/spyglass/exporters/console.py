"""Console exporter (stdout). Collector-ready via __call__(batch)."""

from __future__ import annotations

import json
import sys
from collections.abc import Iterable
from typing import Any, cast

try:
    import orjson as _orjson
except Exception:  # pragma: no cover
    _orjson = None  # type: ignore[assignment]

__all__ = ["ConsoleExporter"]


class ConsoleExporter:
    def __init__(self, *, pretty: bool = False):
        self.pretty = pretty

    def __call__(self, batch: Iterable[dict[str, Any]]) -> None:
        use_orjson = _orjson is not None and not self.pretty

        if use_orjson:
            # Use orjson for fast, compact output
            for obj in batch:
                # Handle both buffer and non-buffer stdout
                if hasattr(sys.stdout, "buffer"):
                    sys.stdout.buffer.write(cast(bytes, cast(Any, _orjson).dumps(obj)))
                    sys.stdout.buffer.write(b"\n")
                else:
                    sys.stdout.write(cast(bytes, cast(Any, _orjson).dumps(obj)).decode())
                    sys.stdout.write("\n")
            sys.stdout.flush()
        else:
            # Use stdlib json (fallback or pretty mode)
            for obj in batch:
                if self.pretty:
                    s = json.dumps(obj, ensure_ascii=False, indent=2)
                else:
                    s = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
                sys.stdout.write(s)
                sys.stdout.write("\n")
            sys.stdout.flush()
