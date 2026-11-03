"""`common.py` — 720p 基準の数と、型のパレット。

尺度が変われば数が変わること、色が型の値そのものであること。
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def load_common():
    spec = importlib.util.spec_from_file_location("common_under_test",
                                                  REPO / "engine" / "common.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_scale_is_applied_to_layout_numbers():
    K = load_common()
    K.SCALE = 1.0
    assert K.S(120) == 120
    assert K.S(0.5) == 0                     # 四捨五入（int(round)）
    assert K.S(12.6) == 13

    K.SCALE = 1.5                            # 1080p（720p の 1.5 倍）
    assert K.S(120) == 180
    assert K.S(1) == 2


def test_palette_lookup_keeps_the_declared_rgb():
    K = load_common()
    K.PAL = {"ink": [32, 35, 42], "white": [255, 255, 255, 255]}
    assert K.C("ink") == (32, 35, 42)
    assert K.C("white") == (255, 255, 255, 255)


def test_ruby_is_stripped_from_subtitles():
    # 字幕は原表記。ルビの括弧だけが落ちる。
    spec = importlib.util.spec_from_file_location("reading_under_test",
                                                  REPO / "engine" / "reading.py")
    reading = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(reading)
    assert reading.strip_ruby("20年《にじゅうねん》前。") == "20年前。"
    assert reading.strip_ruby("そのまま") == "そのまま"
