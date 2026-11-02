#!/usr/bin/env python3
"""台本・映像設定・読みの参照を、機械的に確かめる。

意味の判断はしない。切れている参照・重複・欠けだけを見る。
guide-script が Markdown から YAML へ起こした直後と、焼く前の点検に使う。

  <venv> engine/scriptcheck.py --project projects/<作品>
  <venv> engine/scriptcheck.py --project projects/<作品> --strict
  <venv> engine/scriptcheck.py --project projects/<作品> --json

終了コード: エラーがあれば 1。警告は既定では 0（--strict なら 1）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

import characters as C
import sal_enums

REPO = Path(__file__).resolve().parent.parent
RUBY = re.compile(r"([^\s《》]+)《([^》]+)》")
MAX_SUBTITLE = 27
# 声を持たない行（「……」だけなど）は build_voice.py が落ちる。間は pause_before に置く。
SPEAKABLE = re.compile(r"[ぁ-んァ-ヶ一-鿿a-zA-Z0-9]")
# 読点を一語ずつ打つ書き方（「鏡の、前に、置く、小さな、装置だ。」）を見る。
# 読点の数と、区切りの平均の長さの両方で判定する。片方だけでは、
# 長い文に正しく打った読点まで拾ってしまう。
MIN_COMMA_FLAG = 3
MAX_MEAN_SEGMENT = 4


def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def strip_ruby(text: str) -> str:
    return RUBY.sub(r"\1", text or "")


def cast_ids(name: str) -> set[str] | None:
    path = REPO / "characters" / f"{name}.cast.yaml"
    if not path.exists():
        return None
    cast = load_yaml(path)
    return {c.get("id") for c in cast.get("characters", []) if c.get("id")}


# cue の演技の欄 → SAL の語彙。
VOICE_ENUMS = {
    "emotion": "emotion",
    "speed": "speed",
    "volume": "volume",
    "delivery": "delivery",
    "intensity": "intensity",
}


def check_acting(cue: dict, ids: set[str], faces: dict[str, set[str]],
                 sheets: dict[str, dict | None], enums: dict[str, set[str]],
                 errors: list[str], warnings: list[str]) -> None:
    """演技の欄の参照切れを見る。網羅率などの計測は acting.py の役目。"""
    name = cue.get("name") or "?"
    cid = cue.get("character") or ""

    face = cue.get("face")
    if face:
        if not isinstance(face, str):
            errors.append(f"{name}: face が文字列でない")
        else:
            if str(face).startswith("blink_"):
                errors.append(f"{name}: face {face!r} はまばたき（使わない）")
            if cid and cid in faces and face not in faces[cid]:
                errors.append(f"{name}: face {face!r} が {cid} の expressions に無い")

    for key, enum_key in VOICE_ENUMS.items():
        value = cue.get(key)
        if value is None or value == "":
            continue
        if not isinstance(value, str):
            errors.append(f"{name}: {key} が文字列でない")
            continue
        allowed = enums.get(enum_key)
        if allowed and value not in allowed:
            errors.append(f"{name}: {key} {value!r} が SAL の {enum_key} に無い")

    beat = cue.get("beat")
    if beat:
        sheet = sheets.get(cid)
        if sheet is None:
            warnings.append(f"{name}: beat {beat!r} を検査できない（{cid} の人物票が無い）")
        elif beat not in (sheet.get("emotions") or {}):
            errors.append(f"{name}: beat {beat!r} が {cid} の emotions に無い")

    pb = cue.get("pause_before")
    if pb is not None:
        if not isinstance(pb, (int, float)) or isinstance(pb, bool):
            errors.append(f"{name}: pause_before が数値でない")
        elif pb < 0:
            errors.append(f"{name}: pause_before が負（{pb}）")
        elif pb > 5:
            warnings.append(f"{name}: pause_before が {pb} 秒（長すぎないか）")

    react = cue.get("react")
    if react is None:
        return
    if not isinstance(react, dict):
        errors.append(f"{name}: react が辞書でない")
        return
    for rid, entry in react.items():
        if rid not in ids:
            errors.append(f"{name}: react の {rid!r} が cast に無い")
            continue
        if not isinstance(entry, dict):
            errors.append(f"{name}: react.{rid} が辞書でない")
            continue
        rface = entry.get("face")
        rbeat = entry.get("beat")
        mark = entry.get("mark")
        if not rface and not rbeat and not mark:
            errors.append(f"{name}: react.{rid} に顔も記号も無い")
        if rface:
            if not isinstance(rface, str):
                errors.append(f"{name}: react.{rid}.face が文字列でない")
            else:
                if rface.startswith("blink_"):
                    errors.append(f"{name}: react.{rid}.face {rface!r} はまばたき（使わない）")
                if rid in faces and rface not in faces[rid]:
                    errors.append(f"{name}: react.{rid}.face {rface!r} が "
                                  f"{rid} の expressions に無い")
        if rbeat:
            sheet = sheets.get(rid)
            if sheet is not None and rbeat not in (sheet.get("emotions") or {}):
                errors.append(f"{name}: react.{rid}.beat {rbeat!r} が "
                              f"{rid} の emotions に無い")
            elif sheet is not None and not rface:
                # beat から顔が決まること（決まらないなら face を明示する）
                mapped = ((sheet.get("emotions") or {}).get(rbeat) or {}).get("face")
                if not mapped:
                    errors.append(f"{name}: react.{rid}.beat {rbeat!r} に face が無い"
                                  f"（人物票の emotions に face を書くか、face を明示する）")
                elif rid in faces and mapped not in faces[rid]:
                    errors.append(f"{name}: react.{rid}.beat {rbeat!r} の face "
                                  f"{mapped!r} が {rid} の expressions に無い")
        if mark:
            if not isinstance(mark, str):
                errors.append(f"{name}: react.{rid}.mark が文字列でない")
            elif len(mark) > 3:
                errors.append(f"{name}: react.{rid}.mark が {len(mark)} 字（3 字まで）")


def check_punctuation(name: str, line: str, warnings: list[str]) -> None:
    """読点を一語ずつ打っていないかを見る（日本語の行だけ）。

    「鏡の、前に、置く、小さな、装置だ。」のような行は、声が息継ぎを繰り返し、
    視聴者が文の構造を追えなくなる。読点の数と、区切りの平均の長さの
    両方が小さいときだけ警告する（長い文の正しい読点を拾わないため）。
    """
    if not re.search(r"[ぁ-んァ-ヶ一-鿿]", line):
        return
    commas = line.count("、")
    segments = [s for s in line.split("、") if s]
    if commas >= MIN_COMMA_FLAG and segments:
        mean = sum(len(s) for s in segments) / len(segments)
        if mean <= MAX_MEAN_SEGMENT:
            warnings.append(
                f"{name}: 読点が多すぎる（区切りの平均 {mean:.1f} 字）。"
                f"一語ずつ区切らず、文節の切れ目に打つ: {line!r}"
            )


def check(args) -> int:
    project = Path(args.project)
    errors: list[str] = []
    warnings: list[str] = []

    script_path = project / "script.yaml"
    if not script_path.exists():
        errors.append(f"script.yaml が無い: {script_path}")
        return report(errors, warnings, args)
    script = load_yaml(script_path)
    video = load_yaml(project / "video.yaml") if (project / "video.yaml").exists() else {}
    display = video.get("display") or {}
    cues = script.get("cues") or []
    if not cues:
        errors.append("script.yaml に cues が無い")

    names: list[str] = []
    for i, cue in enumerate(cues, 1):
        name = cue.get("name") or ""
        if not name:
            errors.append(f"cues[{i}]: name が無い")
            continue
        names.append(name)
        line = (cue.get("line") or "").strip()
        if not line:
            errors.append(f"{name}: line が空")
        elif not SPEAKABLE.search(strip_ruby(line)):
            errors.append(
                f"{name}: 声を持たない行（{line!r}）。間は次の cue の pause_before に置く"
            )
        else:
            check_punctuation(name, strip_ruby(line), warnings)
    dupes = sorted({n for n in names if names.count(n) > 1})
    for name in dupes:
        errors.append(f"cue 名が重複している: {name}")
    name_set = set(names)

    if video.get("cast"):
        cast_name = video["cast"]
        ids = cast_ids(cast_name)
        if ids is None:
            errors.append(f"cast が無い: characters/{cast_name}.cast.yaml")
        else:
            cast_doc = load_yaml(REPO / "characters" / f"{cast_name}.cast.yaml")
            faces = {c.get("id"): set(c.get("expressions") or [])
                     for c in cast_doc.get("characters", []) if c.get("id")}
            sheets = {cid: C.sheet_for_cast(cast_name, cid) for cid in ids}
            enums = sal_enums.load()
            if not enums and any(cue.get(k) for cue in cues for k in VOICE_ENUMS):
                warnings.append("SAL の語彙が読めない（SAL= で場所を指定）。"
                                "声の語彙の検査は飛ばした")
            for cue in cues:
                cid = cue.get("character") or ""
                if cid and cid not in ids:
                    errors.append(f"{cue.get('name')}: character {cid!r} が cast に無い")
                check_acting(cue, ids, faces, sheets, enums, errors, warnings)

    template = video.get("template") or ""
    if template and not (REPO / "references" / "templates" / template / "template.yaml").exists():
        errors.append(f"型が無い: references/templates/{template}/template.yaml")

    for name in sorted(set(display) - name_set):
        errors.append(f"video.yaml display: script.yaml に無い cue {name}")
    for name in sorted((video.get("chapters") or {}).keys() - name_set):
        errors.append(f"video.yaml chapters: script.yaml に無い cue {name}")

    chime_path = project / "chapters.yaml"
    if chime_path.exists():
        chimes = load_yaml(chime_path)
        if isinstance(chimes, list):
            for name in chimes:
                if name not in name_set:
                    errors.append(f"chapters.yaml: script.yaml に無い cue {name}")
            video_ch = set((video.get("chapters") or {}).keys())
            if video_ch and set(chimes) != video_ch:
                warnings.append(
                    f"chapters.yaml と video.yaml の章が違う（チャイム {len(chimes)} / 札 {len(video_ch)}）"
                )
        else:
            errors.append("chapters.yaml は cue 名の配列であること")
        if isinstance(chimes, list) and chimes and not (project / "assets" / "sfx" / "chime.wav").exists():
            warnings.append(
                "chapters.yaml があるが assets/sfx/chime.wav が無い（章の印が鳴らない）"
            )

    reading_path = project / "reading.yaml"
    if reading_path.exists():
        readings = (load_yaml(reading_path).get("readings") or {})
        for name in names:
            if not readings.get(name):
                warnings.append(f"{name}: reading.yaml に読みが無い")
        for name in sorted(set(readings) - name_set):
            errors.append(f"reading.yaml: script.yaml に無い cue {name}")

    for cue in cues:
        name = cue.get("name") or "?"
        text = strip_ruby(display.get(name) or cue.get("line", ""))
        if len(text) > MAX_SUBTITLE:
            warnings.append(f"{name}: 字幕が {len(text)} 字（{MAX_SUBTITLE} 字超）")

    return report(errors, warnings, args, counts=(len(names), len(video.get("chapters") or {})))


def report(errors: list[str], warnings: list[str], args, counts: tuple[int, int] | None = None) -> int:
    if args.json:
        print(json.dumps({"ok": not errors, "errors": errors, "warnings": warnings},
                         ensure_ascii=False, indent=2))
    else:
        if counts:
            print(f"{counts[0]} cue / {counts[1]} 章")
        if errors:
            print(f"エラー {len(errors)} 件")
            for line in errors:
                print(f"  {line}")
        if warnings:
            print(f"警告 {len(warnings)} 件")
            for line in warnings:
                print(f"  {line}")
        if not errors and not warnings:
            print("ok")
        elif not errors:
            print("エラーなし")
    if errors:
        return 1
    if warnings and args.strict:
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="台本・映像設定・読みの参照を確かめる。")
    ap.add_argument("--project", required=True)
    ap.add_argument("--strict", action="store_true", help="警告も失敗として扱う")
    ap.add_argument("--json", action="store_true")
    return check(ap.parse_args())


if __name__ == "__main__":
    sys.exit(main())
