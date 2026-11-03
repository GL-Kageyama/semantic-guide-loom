"""`bgm.py` の計画と署名 — 同じ入力から同じシード・同じ署名。

音そのものは作らない（MusicGen は重い）。入力の解釈だけを試す。
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


def load_bgm():
    spec = importlib.util.spec_from_file_location("bgm_under_test", REPO / "engine" / "bgm.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bgm():
    return load_bgm()


def test_auto_seeds_are_stable(bgm):
    first = bgm.auto_seeds("同じプロンプト", 3)
    second = bgm.auto_seeds("同じプロンプト", 3)
    assert first == second
    assert len(set(first)) == 3          # 同じ本の中で重ならない


def test_auto_seeds_follow_the_prompt(bgm):
    assert bgm.auto_seeds("A", 3) != bgm.auto_seeds("B", 3)


def test_signature_changes_when_input_changes(bgm):
    cfg = {"prompt": "A", "segment_s": 30, "crossfade_s": 2.5}
    seeds = [1, 2, 3]
    base = bgm.signature(cfg, 90.0, seeds)
    assert base == bgm.signature(dict(cfg), 90.0, list(seeds))
    assert base != bgm.signature({**cfg, "prompt": "B"}, 90.0, seeds)
    assert base != bgm.signature(cfg, 90.0, [1, 2, 4])


def test_plan_counts_segments(bgm, tmp_path):
    cfg = {"prompt": "A", "segment_s": 30, "seeds": "auto"}
    plan = bgm.plan(cfg, tmp_path, None)
    assert plan["count"] == 3             # 90 秒 / 30 秒
    assert len(plan["seeds"]) == 3

    short = bgm.plan({**cfg, "segment_s": 10}, tmp_path, None)
    assert short["count"] == 9


def test_plan_rejects_more_than_musicgen_can(bgm, tmp_path):
    with pytest.raises(SystemExit):
        bgm.plan({"prompt": "A", "segment_s": 31, "seeds": "auto"}, tmp_path, None)


def test_plan_rejects_too_few_seeds(bgm, tmp_path):
    with pytest.raises(SystemExit) as exc:
        bgm.plan({"prompt": "A", "segment_s": 30, "seeds": [1, 2]}, tmp_path, None)
    assert "seeds" in str(exc.value)


def test_plan_reads_duration_from_mix(bgm, tmp_path):
    (tmp_path / "mix.yaml").write_text("duration: 61.5\n", encoding="utf-8")
    plan = bgm.plan({"prompt": "A", "segment_s": 30, "seeds": "auto",
                     "duration": "auto"}, tmp_path, None)
    assert plan["count"] == 3             # 61.5 秒 → 30+30+1.5
    assert plan["duration"] == 61.5
