#!/usr/bin/env python3
"""timeline.json・型・キャストから、解説動画を描いて ffmpeg へ流す。

  <venv> render.py --timeline timeline.json --out ../out/cyber-basics.mp4
  <venv> render.py --timeline timeline.json --still 40.0      # 1 枚だけ出す
  <venv> render.py --timeline timeline.json --start 0 --duration 15 --out preview.mp4

型（templates/<name>/template.yaml）が持つのは **絵の側** ——画布・色・書体・
立ち位置・札・字幕・上段・進捗・間合い。作品（timeline.json）が持つのは
**意味の側** ——題・章・字幕・時刻。キャスト（casts/<name>.cast.yaml）が持つのは
**誰が居るか** ——表情シート・口パクの有無・動き・拡大率。

この入口がやるのは 4 つだけ——読む・型を選ぶ・1 コマずつ描く・ffmpeg へ流す。
並べ方そのものは engine/layouts/<型>.py にある（型が `layout:` で名乗る）。
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))

import common as K  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", default=str(HERE / "timeline.json"))
    ap.add_argument("--template", default="", help="型の名（既定は timeline.json の template）")
    ap.add_argument("--cast", default="", help="キャストの名（既定は timeline.json の cast）")
    ap.add_argument("--out", default="")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--duration", type=float, default=0.0)
    ap.add_argument("--still", type=float, default=None)
    ap.add_argument("--fps", type=int, default=0)
    ap.add_argument("--crf", type=int, default=20)
    ap.add_argument("--preset", default="veryfast")
    args = ap.parse_args()

    tl = json.load(open(args.timeline, encoding="utf-8"))
    tname = args.template or tl.get("template") or ""
    cname = args.cast or tl.get("cast") or ""
    if not tname:
        ap.error("型が決まらない（--template か video.yaml の template）")

    K.TPL = K.load_yaml(REPO / "templates" / tname / "template.yaml")
    K.PAL = K.TPL["palette"]
    W, H = int(tl["width"]), int(tl["height"])
    K.SCALE = H / float(K.TPL["canvas"]["height"])
    K.ASSETS = str(REPO / "build" / tl["name"] / "assets")
    fps = args.fps or int(tl["fps"])

    cast = None
    if cname:
        cast = K.Cast(K.load_yaml(REPO / "casts" / f"{cname}.cast.yaml"),
                      float(K.TPL.get("dim_when_silent", 1.0)))

    layout = importlib.import_module(f"layouts.{K.TPL.get('layout', 'dialogue_bust')}")
    draw_frame = layout.build(tl, cast, fps, W, H)

    if args.still is not None:
        t = float(args.still)
        im = draw_frame(t, int(t * fps))
        out = args.out or str(HERE / f"still_{t:.0f}.png")
        im.save(out)
        print(out)
        return

    total_frames = int(round(tl["duration"] * fps))
    start = max(0.0, args.start)
    dur = args.duration if args.duration > 0 else max(0.0, tl["duration"] - start)
    f0 = int(round(start * fps))
    f1 = min(total_frames, int(round((start + dur) * fps)))
    out = args.out or str(REPO / "out" / f"{tl['name']}.mp4")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)

    audio = tl.get("audio", "")
    cmd = ["ffmpeg", "-y", "-loglevel", "warning",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps),
           "-i", "pipe:0"]
    if os.path.exists(audio):
        cmd += ["-ss", f"{start:.3f}", "-i", audio]
    cmd += ["-c:v", "libx264", "-preset", args.preset, "-crf", str(args.crf),
            "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
    if os.path.exists(audio):
        cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += [out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    try:
        for fi in range(f0, f1):
            im = draw_frame(fi / fps, fi)
            proc.stdin.write(im.tobytes())
            if (fi - f0) % (fps * 30) == 0:
                print(f"  {fi - f0}/{f1 - f0}", flush=True)
    finally:
        proc.stdin.close()
        proc.wait()
    print(out)


if __name__ == "__main__":
    main()
