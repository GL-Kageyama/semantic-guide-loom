"""`export_timeline.py` — 時刻は mix.yaml の実尺から来る。

守るのは 3 つ。cue の頭尾が WAV の実尺から出ること、章の札が型の `chapter_lead`
だけ手前から出ること、詳細カードの `start` が cue の実尺へ解決されること。
"""
from __future__ import annotations

import json
import wave

import yaml


def write_wav(path, seconds: float, sr: int = 8000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(b"\0\0" * int(sr * seconds))


def make_project(tmp_path, duration: float = 10.0, details: bool = True):
    project = tmp_path / "demo-work"
    (project / "assets" / "voice").mkdir(parents=True)

    script = {
        "name": "demo-work",
        "default_pause": 0.25,
        "cues": [
            {"name": "c01", "character": "mirai", "line": "一つ目。"},
            {"name": "c02", "character": "mirabo", "line": "二つ目。"},
            {"name": "c03", "character": "mirai", "line": "三つ目。"},
            {"name": "c04", "character": "mirai", "line": "章の外。"},
        ],
    }
    chapter = {
        "label": "第1章",
        "title": "章の題",
        "term": "章",
        "key": "一章の要約。",
    }
    if details:
        chapter["details"] = [
            {"cue": "c02", "head": "詳細", "lines": ["一つ", "二つ"]},
        ]
    video = {
        "title": "見本",
        "template": "dialogue-bust",
        "fps": 30,
        "width": 1280,
        "height": 720,
        "chapters": {"c01": chapter},
    }
    mix = {
        "duration": duration,
        "stems": [
            {"role": "voice", "start": 1.0, "file": "assets/voice/c01.wav"},
            {"role": "voice", "start": 3.0, "file": "assets/voice/c02.wav"},
            {"role": "voice", "start": 5.0, "file": "assets/voice/c03.wav"},
            {"role": "voice", "start": 7.0, "file": "assets/voice/c04.wav"},
            {"role": "bed", "start": 0.0, "file": "assets/bgm/underlay.wav"},
        ],
    }
    (project / "script.yaml").write_text(
        yaml.safe_dump(script, allow_unicode=True), encoding="utf-8")
    (project / "video.yaml").write_text(
        yaml.safe_dump(video, allow_unicode=True), encoding="utf-8")
    (project / "mix.yaml").write_text(
        yaml.safe_dump(mix, allow_unicode=True), encoding="utf-8")

    for index, name in enumerate(("c01", "c02", "c03", "c04")):
        # 実尺を 1 秒ずつ変える（start は 1,3,5,7 秒）
        write_wav(project / "assets" / "voice" / f"{name}.wav", 1.0 + index * 0.25)
    return project


def run(run_engine, project, out):
    return run_engine("export_timeline.py", "--project", str(project), "--out", str(out))


def test_cues_come_from_wav_durations(run_engine, tmp_path):
    project = make_project(tmp_path)
    out = tmp_path / "timeline.json"
    result = run(run_engine, project, out)
    assert result.returncode == 0, result.stderr

    tl = json.loads(out.read_text(encoding="utf-8"))
    by_name = {c["name"]: c for c in tl["cues"]}
    assert by_name["c01"]["start"] == 1.0
    assert by_name["c01"]["end"] == 2.0          # 1.0 秒の WAV
    assert by_name["c02"]["end"] == 4.25         # 1.25 秒の WAV
    assert tl["duration"] == 10.0


def test_chapter_starts_lead_before_its_cue(run_engine, tmp_path, template_lead):
    project = make_project(tmp_path)
    out = tmp_path / "timeline.json"
    assert run(run_engine, project, out).returncode == 0

    tl = json.loads(out.read_text(encoding="utf-8"))
    chapter = tl["chapters"][0]
    lead = template_lead("dialogue-bust")
    assert chapter["cue_start"] == 1.0
    assert chapter["start"] == round(max(0.0, 1.0 - lead), 4)


def test_detail_start_is_resolved_to_the_cue(run_engine, tmp_path):
    project = make_project(tmp_path)
    out = tmp_path / "timeline.json"
    assert run(run_engine, project, out).returncode == 0

    tl = json.loads(out.read_text(encoding="utf-8"))
    details = tl["chapters"][0]["details"]
    assert details[0]["cue"] == "c02"
    assert details[0]["start"] == 3.0            # c02 の mix 上の頭


def test_cue_after_the_chapter_belongs_to_it(run_engine, tmp_path):
    project = make_project(tmp_path)
    out = tmp_path / "timeline.json"
    assert run(run_engine, project, out).returncode == 0

    tl = json.loads(out.read_text(encoding="utf-8"))
    by_name = {c["name"]: c for c in tl["cues"]}
    assert by_name["c01"]["chapter"] == 0
    assert by_name["c04"]["chapter"] == 0        # 章の区切りに居ない cue は直前の章へ


def test_short_detail_is_a_warning_not_a_failure(run_engine, tmp_path):
    # 詳細が 3.0 秒から、作品の終わり 5.5 秒まで ＝ 可視 2.5 秒
    project = make_project(tmp_path, duration=5.5)
    out = tmp_path / "timeline.json"
    result = run(run_engine, project, out)
    assert result.returncode == 0                # 実尺で変わるので止めない
    assert "4.0 秒未満" in result.stderr
    assert out.exists()


def test_missing_voice_stem_fails(run_engine, tmp_path):
    project = make_project(tmp_path)
    mix_path = project / "mix.yaml"
    mix = yaml.safe_load(mix_path.read_text(encoding="utf-8"))
    mix["stems"] = [s for s in mix["stems"] if "c03" not in s["file"]]
    mix_path.write_text(yaml.safe_dump(mix, allow_unicode=True), encoding="utf-8")

    result = run(run_engine, project, tmp_path / "timeline.json")
    assert result.returncode != 0
    assert "c03" in result.stderr
