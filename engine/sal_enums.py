#!/usr/bin/env python3
"""semantic-audio-loom の演技語彙を、SAL の schema から読む。

写さない。SAL が無い環境では空の辞書を返し、呼び出し側は語彙の検査を飛ばす。
音の語彙の正本は SAL の `schemas/scene.schema.json`。
"""
from __future__ import annotations

import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def sal_root() -> Path:
    """SAL の場所。`SAL=` で変えられる（engine/bgm.py と同じ規則）。"""
    return Path(os.environ.get("SAL", REPO.parent / "semantic-audio-loom"))


def load() -> dict[str, set[str]]:
    """cue が持てる演技の語彙。読めなければ空。"""
    path = sal_root() / "schemas" / "scene.schema.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    items = ((((data.get("properties") or {}).get("cues") or {}).get("items") or {}))
    props = items.get("properties") or {}
    out: dict[str, set[str]] = {}
    for key, spec in props.items():
        if isinstance(spec, dict) and isinstance(spec.get("enum"), list):
            out[key] = {str(v) for v in spec["enum"]}
    return out
