"""1 コマは状態を持たない — `--still` は何度でも同じ絵。

real の入口（render.py）を通す。同じ時刻を 2 回出してバイト一致、
違う時刻とは違うこと（**一致が空振りでないこと**）も見る。
"""
from __future__ import annotations

import hashlib
import json


def make_timeline(tmp_path):
    timeline = {
        "name": "demo",
        "template": "narrate-slide",
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "duration": 10.0,
        "title": "見本の題",
        "channel": "",
        "cues": [
            {"name": "c01", "start": 0.0, "end": 2.5, "text": "一つ目の話。"},
            {"name": "c02", "start": 2.5, "end": 6.0, "text": "二つ目の話。"},
        ],
        "chapters": [
            {"index": 0, "start": 0.0, "label": "第1章", "title": "章の題",
             "bullets": ["一つ", "二つ"]},
        ],
    }
    path = tmp_path / "timeline.json"
    path.write_text(json.dumps(timeline, ensure_ascii=False), encoding="utf-8")
    return path


def still(run_engine, timeline, t, out):
    return run_engine("render.py", "--timeline", str(timeline),
                      "--still", str(t), "--out", str(out))


def digest(path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def test_same_time_same_frame(run_engine, tmp_path):
    timeline = make_timeline(tmp_path)
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    assert still(run_engine, timeline, 3.0, a).returncode == 0
    assert still(run_engine, timeline, 3.0, b).returncode == 0
    assert digest(a) == digest(b)


def test_different_time_different_frame(run_engine, tmp_path):
    timeline = make_timeline(tmp_path)
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    assert still(run_engine, timeline, 1.0, a).returncode == 0
    assert still(run_engine, timeline, 4.0, b).returncode == 0
    assert digest(a) != digest(b)


def test_still_comes_from_the_requested_time_not_frame_zero(run_engine, tmp_path):
    timeline = make_timeline(tmp_path)
    t0, t4 = tmp_path / "t0.png", tmp_path / "t4.png"
    assert still(run_engine, timeline, 0.0, t0).returncode == 0
    assert still(run_engine, timeline, 4.0, t4).returncode == 0
    # 4 秒のコマは、0 秒のコマの写しではない（字幕が二つ目に替わっている）
    assert digest(t0) != digest(t4)
