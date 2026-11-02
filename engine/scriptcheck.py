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

REPO = Path(__file__).resolve().parent.parent
RUBY = re.compile(r"([^\s《》]+)《([^》]+)》")
MAX_SUBTITLE = 27
# 声を持たない行（「……」だけなど）は build_voice.py が落ちる。間は pause_before に置く。
SPEAKABLE = re.compile(r"[ぁ-んァ-ヶ一-鿿a-zA-Z0-9]")


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
    dupes = sorted({n for n in names if names.count(n) > 1})
    for name in dupes:
        errors.append(f"cue 名が重複している: {name}")
    name_set = set(names)

    if video.get("cast"):
        ids = cast_ids(video["cast"])
        if ids is None:
            errors.append(f"cast が無い: characters/{video['cast']}.cast.yaml")
        else:
            for cue in cues:
                cid = cue.get("character") or ""
                if cid and cid not in ids:
                    errors.append(f"{cue.get('name')}: character {cid!r} が cast に無い")

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
