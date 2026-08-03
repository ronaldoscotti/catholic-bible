"""The published OpenAPI document.

Rendering lives here rather than in the script so the test and the CI gate
compare the same bytes. Two renderers drift, and the drift shows up as a
document that passes locally and fails on a push.
"""

from __future__ import annotations

import json
from pathlib import Path

from catholic_bible.api.app import app

PATH = Path(__file__).resolve().parents[3] / "openapi.json"


def rendered() -> str:
    return (
        json.dumps(app.openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
