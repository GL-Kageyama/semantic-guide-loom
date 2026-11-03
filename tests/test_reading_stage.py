"""`reading.py stage` — 舞台は作品を書き換えない。

`line` だけが読みに替わり、字幕の `display` には原表記が残る。元の作品は触らない。
"""
from __future__ import annotations

import hashlib

import yaml


def write(path, doc):
    path.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False),
                    encoding="utf-8")


def make_project(tmp_path):
    project = tmp_path / "work"
    project.mkdir()
    script = {
        "name": "work",
        "cues": [
            {"name": "c01", "character": "a", "line": "20年《にじゅうねん》前。"},
            {"name": "c02", "character": "a", "line": "十年後。"},
        ],
    }
    video = {
        "title": "題",
        "template": "narrate-slide",
        "display": {"c02": "十年後。"},
        "chapters": {},
    }
    reading = {"name": "work", "readings": {"c01": "にじゅうねんまえ。",
                                            "c02": "じゅうねんご。"}}
    write(project / "script.yaml", script)
    write(project / "video.yaml", video)
    write(project / "reading.yaml", reading)
    return project


def digest(path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def test_stage_replaces_line_and_keeps_display(run_engine, tmp_path):
    project = make_project(tmp_path)
    before = {p.name: digest(p) for p in project.iterdir()}
    stage = tmp_path / "stage"

    result = run_engine("reading.py", "stage", "--project", str(project),
                        "--stage", str(stage))
    assert result.returncode == 0, result.stderr

    staged_script = yaml.safe_load((stage / "script.yaml").read_text(encoding="utf-8"))
    staged_video = yaml.safe_load((stage / "video.yaml").read_text(encoding="utf-8"))
    cues = {c["name"]: c for c in staged_script["cues"]}

    assert cues["c01"]["line"] == "にじゅうねんまえ。"
    assert cues["c02"]["line"] == "じゅうねんご。"
    # display は原表記。ルビは落ちる。
    assert staged_video["display"]["c01"] == "20年前。"
    assert staged_video["display"]["c02"] == "十年後。"


def test_stage_does_not_touch_the_project(run_engine, tmp_path):
    project = make_project(tmp_path)
    before = {p.name: digest(p) for p in project.iterdir()}

    assert run_engine("reading.py", "stage", "--project", str(project),
                      "--stage", str(tmp_path / "stage")).returncode == 0
    assert {p.name: digest(p) for p in project.iterdir()} == before


def test_missing_reading_fails(run_engine, tmp_path):
    project = make_project(tmp_path)
    (project / "reading.yaml").unlink()

    result = run_engine("reading.py", "stage", "--project", str(project),
                        "--stage", str(tmp_path / "stage"))
    assert result.returncode != 0
    assert "読みが無い" in (result.stdout + result.stderr)


def test_audit_strict_fails_on_kanji_left_in_reading(run_engine, tmp_path):
    project = make_project(tmp_path)
    write(project / "reading.yaml",
          {"name": "work", "readings": {"c01": "二十年まえ。", "c02": "じゅうねんご。"}})

    loose = run_engine("reading.py", "audit", "--project", str(project))
    assert loose.returncode == 0          # 警告だけでは止めない
    assert "漢字" in loose.stdout

    strict = run_engine("reading.py", "audit", "--project", str(project), "--strict")
    assert strict.returncode == 1


def test_audit_reports_missing_and_unknown_cues(run_engine, tmp_path):
    project = make_project(tmp_path)
    write(project / "reading.yaml",
          {"name": "work", "readings": {"c01": "にじゅうねんまえ。", "c09": "よみ"}})

    result = run_engine("reading.py", "audit", "--project", str(project))
    assert result.returncode == 0
    assert "c02: 読みが無い" in result.stdout
    assert "c09: script.yaml に無い cue" in result.stdout
