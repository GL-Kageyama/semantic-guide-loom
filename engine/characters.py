#!/usr/bin/env python3
"""キャラクタのデータを、1 か所で読む。

    characters/<キャスト>.cast.yaml      絵の側（表情シート・口・動き）
    characters/<キャスト>.persona.yaml   二人（以上）の関係
    characters/<id>.character.yaml       人物造形（1 人 1 ファイル）

旧形式（persona.yaml に `characters[]` を埋め込んだもの）も読む。
名前はコードに書かない。id はデータから読む。
"""
from __future__ import annotations

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent


def read_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def cast_path(name: str) -> Path:
    return REPO / "characters" / f"{name}.cast.yaml"


def persona_path(name: str) -> Path:
    return REPO / "characters" / f"{name}.persona.yaml"


def character_path(cid: str) -> Path:
    return REPO / "characters" / f"{cid}.character.yaml"


def load_cast(name: str) -> dict:
    path = cast_path(name)
    if not path.exists():
        raise SystemExit(f"cast が無い: {path}")
    return read_yaml(path)


def load_persona(name: str) -> dict:
    path = persona_path(name)
    if not path.exists():
        raise SystemExit(f"persona が無い: {path}")
    return read_yaml(path)


def load_character(cid: str) -> dict | None:
    path = character_path(cid)
    if not path.exists():
        return None
    return read_yaml(path)


def cast_ids(cast: dict) -> list[str]:
    return [c["id"] for c in cast.get("characters", []) if c.get("id")]


def legacy_by_id(persona: dict) -> dict[str, dict]:
    return {c["id"]: c for c in persona.get("characters", []) if c.get("id")}


def sheet_for_cast(name: str, cid: str, persona: dict | None = None) -> dict | None:
    """1 人ぶんの人物票。新しいファイルが優先。無ければ旧形式。"""
    sheet = load_character(cid)
    if sheet is not None:
        return sheet
    persona = persona if persona is not None else read_yaml(persona_path(name))
    return legacy_by_id(persona).get(cid)


def sheets_for_cast(name: str) -> list[dict]:
    """cast の並び順で、人物票を返す。無い id は飛ばす（検査は persona.py がする）。"""
    cast = read_yaml(cast_path(name))
    persona = read_yaml(persona_path(name))
    out: list[dict] = []
    for cid in cast_ids(cast):
        sheet = sheet_for_cast(name, cid, persona)
        if sheet is not None:
            out.append(sheet)
    return out


def expressions(cast: dict, cid: str) -> set[str]:
    for c in cast.get("characters", []):
        if c.get("id") == cid:
            return set(c.get("expressions") or [])
    return set()


def resolve_face(cue: dict | None, faces: set[str], spec: dict,
                 sheet: dict | None) -> tuple[str, bool]:
    """cue から表情を決める。返すのは (表情, 明示か)。

    明示の face → beat（人物票の emotions.<beat>.face）→ emotion の対応表。
    どれも当たらなければ ("", False)。既定は決めない（呼ぶ側が決める）。

    **beat が演技の正本。** face は省略してよく、人物票から解決される。
    """
    if not cue:
        return "", False
    face = cue.get("face") or ""
    if face in faces:
        return face, True
    beat_face = str((beat_spec(sheet, cue.get("beat")) or {}).get("face") or "")
    if beat_face in faces:
        return beat_face, False
    mapped = (spec.get("by_emotion") or {}).get(cue.get("emotion") or "")
    if mapped in faces:
        return mapped, False
    return "", False


def face_for(cast: dict, cid: str, cue: dict | None,
             sheet: dict | None = None) -> str:
    """台本の cue から表情を決める（上と同じ規則）。無ければ既定。"""
    spec = {}
    for c in cast.get("characters", []):
        if c.get("id") == cid:
            spec = c
            break
    faces = set(spec.get("expressions") or [])
    default = cast.get("default_expression") or "neutral"
    face, _ = resolve_face(cue, faces, spec, sheet)
    return face or (default if default in faces else next(iter(faces), default))


def motion_gain(cast: dict, cid: str, face: str) -> float:
    """表情ごとの身体の揺れの倍率。未記載は 1.0。"""
    for c in cast.get("characters", []):
        if c.get("id") == cid:
            return float((c.get("motion_gain") or {}).get(face, 1.0))
    return 1.0


def beat_spec(sheet: dict | None, beat: str | None) -> dict:
    """人物票の感情の型（beat）を引く。無ければ空。"""
    if not sheet or not beat:
        return {}
    value = (sheet.get("emotions") or {}).get(beat)
    return value if isinstance(value, dict) else {}
