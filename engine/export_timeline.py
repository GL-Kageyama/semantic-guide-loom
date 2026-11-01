#!/usr/bin/env python3
"""作品の台本・ミックス・映像設定から、描画用の timeline.json を書く。

読み手は render.py だけ。semantic-audio-loom の内側（mix.yaml / script.yaml）を
知るのはこの道具だけで済むようにしてある。

  PYTHONPATH=. <venv> export_timeline.py \
      --project ../../semantic-guide-loom/projects/cyber-basics \
      --out timeline.json

時刻の出どころは mix.yaml の voice stem（assemble.py が実尺から書いたもの）。
台本の pause_before を自前で足し直さない。足し直すと声と 1 フレームずつずれる。

型とキャストの名は video.yaml が持つ（`template:` / `cast:`）。この道具は
その名を timeline.json へ写すだけで、中身は読まない。読むのは章の出だけ——
札を cue の何秒前から出すかは型の `timing.chapter_lead` が決める。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import wave
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


def wav_duration(path: str) -> float:
    with wave.open(path, "rb") as w:
        return w.getnframes() / float(w.getframerate())


def chapter_lead(template: str) -> float:
    """型が「札を cue の何秒前から出すか」を持つ。無ければ 1.6 秒。"""
    if not template:
        return 1.6
    p = REPO / "references" / "templates" / template / "template.yaml"
    if not p.exists():
        sys.exit(f"型が無い: {p}")
    with open(p, encoding="utf-8") as f:
        tpl = yaml.safe_load(f) or {}
    return float((tpl.get("timing") or {}).get("chapter_lead", 1.6))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, help="script.yaml のあるディレクトリ")
    ap.add_argument("--out", default="timeline.json")
    ap.add_argument("--fps", type=int, default=0, help="既定は video.yaml の fps（無ければ 30）")
    ap.add_argument("--width", type=int, default=0)
    ap.add_argument("--height", type=int, default=0)
    ap.add_argument("--audio", default="", help="焼いた WAV（既定は renders/<name>.wav）")
    args = ap.parse_args()

    work = os.path.abspath(args.project)
    name = os.path.basename(work.rstrip("/"))
    with open(os.path.join(work, "script.yaml"), encoding="utf-8") as f:
        script = yaml.safe_load(f)
    with open(os.path.join(work, "mix.yaml"), encoding="utf-8") as f:
        mix = yaml.safe_load(f)
    vpath = os.path.join(work, "video.yaml")
    video = {}
    if os.path.exists(vpath):
        with open(vpath, encoding="utf-8") as f:
            video = yaml.safe_load(f) or {}
    display = video.get("display", {}) or {}
    template = video.get("template", "") or ""
    cast = video.get("cast", "") or ""
    lead = chapter_lead(template)

    # voice stem の頭を cue 名で引く
    starts: dict[str, tuple[float, str]] = {}
    for stem in mix["stems"]:
        if stem.get("role") != "voice":
            continue
        p = os.path.normpath(os.path.join(work, stem["file"]))
        starts[os.path.splitext(os.path.basename(p))[0]] = (float(stem["start"]), p)

    chapters = video.get("chapters", {}) or {}
    cues = []
    ch_list = []
    for i, cue in enumerate(script["cues"]):
        cue_name = cue.get("name", "")
        if cue_name not in starts:
            sys.exit(f"mix.yaml に voice stem が無い: {cue_name}")
        start, wav = starts[cue_name]
        end = start + wav_duration(wav)
        text = display.get(cue_name) or cue.get("line", "")
        entry = {
            "name": cue_name,
            "character": cue.get("character", ""),
            "start": round(start, 4),
            "end": round(end, 4),
            "wav": wav,
            "text": text,
            "chapter": -1,
            # 表情は cue の側で決める。face が無ければ emotion から引く（描く側で対応表を持つ）
            "emotion": cue.get("emotion", "") or "",
            "face": cue.get("face", "") or "",
        }
        if cue_name in chapters:
            ch = chapters[cue_name] or {}
            entry["chapter"] = len(ch_list)
            # 章の中身は型が決める。ここは素通しする（dialogue-bust は term/key、
            # narrate-slide は bullets を読む）。
            ch_list.append({
                **ch,
                "cue": cue_name,
                "index": len(ch_list),
                "label": ch.get("label", ""),
                "title": ch.get("title", ""),
                "key": ch.get("key", ""),
                "term": ch.get("term", ""),
                # 章の札はチャイムに合わせて cue の手前から出す（何秒手前かは型が持つ）
                "start": round(max(0.0, start - lead), 4),
                "cue_start": round(start, 4),
            })
        cues.append(entry)

    # 章の区切りに居ない cue は直前の章に属す
    cur = -1
    for c in cues:
        if c["chapter"] >= 0:
            cur = c["chapter"]
        c["chapter"] = cur

    audio = args.audio or os.path.join(work, "assets", "renders", name + ".wav")
    tl = {
        "name": name,
        # 作品の置き場。render.py が既定の書き出し先（<project>/renders/<name>.mp4）を決めるのに使う。
        "project": work,
        "title": video.get("title", name),
        "subtitle": video.get("subtitle", ""),
        "channel": video.get("channel", ""),
        "template": template,
        "cast": cast,
        "fps": args.fps or int(video.get("fps", 30)),
        "width": args.width or int(video.get("width", 1280)),
        "height": args.height or int(video.get("height", 720)),
        "duration": round(float(mix.get("duration") or max(c["end"] for c in cues) + 2.5), 4),
        "audio": os.path.abspath(audio),
        "cues": cues,
        "chapters": ch_list,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(tl, f, ensure_ascii=False, indent=1)
    print(f"{args.out}: {len(cues)} cues / {len(ch_list)} chapters / {tl['duration']:.1f}s")


if __name__ == "__main__":
    main()
