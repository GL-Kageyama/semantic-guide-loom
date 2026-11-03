"""`scriptcheck.py` — 参照の切れを見る検査。

本物の作品が緑であることと、事実の参照を外した作品が赤になることの両方を見る。
"""
from __future__ import annotations

import yaml


def write(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False),
                    encoding="utf-8")


def make_research_project(tmp_path, fact="f1"):
    project = tmp_path / "work"
    script = {
        "name": "work",
        "cues": [
            {"name": "c01", "line": "一章の話。"},
            {"name": "c02", "line": "詳細の話。"},
        ],
    }
    video = {
        "title": "題",
        "template": "narrate-slide",
        "chapters": {
            "c01": {
                "label": "第1章",
                "title": "章の題",
                "details": [
                    {"cue": "c02", "head": "要点", "lines": ["一つ", "二つ"],
                     "fact": fact},
                ],
            },
        },
    }
    write(project / "script.yaml", script)
    write(project / "video.yaml", video)
    write(project / "research" / "sources.yaml", {
        "sources": [{
            "id": "s1", "title": "資料", "kind": "reference",
            "url": "https://example.com/", "accessed": "2026-01-01",
            "confidence": "high",
        }],
    })
    write(project / "research" / "facts.yaml", {
        "facts": [{
            "id": "f1", "statement": "検証した事実。", "sources": ["s1"],
            "confidence": "high",
        }],
    })
    return project


def test_real_work_passes(run_engine):
    result = run_engine("scriptcheck.py", "--project", str(
        __import__("pathlib").Path(__file__).resolve().parent.parent
        / "projects" / "making-a-guide"))
    assert result.returncode == 0, result.stdout + result.stderr


def test_resolved_fact_passes(run_engine, tmp_path):
    project = make_research_project(tmp_path)
    result = run_engine("scriptcheck.py", "--project", str(project))
    assert result.returncode == 0, result.stdout + result.stderr


def test_unknown_fact_fails(run_engine, tmp_path):
    project = make_research_project(tmp_path, fact="f2")
    result = run_engine("scriptcheck.py", "--project", str(project))
    assert result.returncode == 1
    assert "research/facts.yaml に無い" in result.stdout


def test_low_confidence_fact_warns(run_engine, tmp_path):
    project = make_research_project(tmp_path)
    write(project / "research" / "facts.yaml", {
        "facts": [{
            "id": "f1", "statement": "未確認の事実。", "sources": ["s1"],
            "confidence": "low",
        }],
    })
    loose = run_engine("scriptcheck.py", "--project", str(project))
    assert loose.returncode == 0
    assert "confidence: low" in loose.stdout

    strict = run_engine("scriptcheck.py", "--project", str(project), "--strict")
    assert strict.returncode == 1


def test_detail_outside_its_chapter_fails(run_engine, tmp_path):
    project = make_research_project(tmp_path)
    video = yaml.safe_load((project / "video.yaml").read_text(encoding="utf-8"))
    video["chapters"]["c01"]["details"].append(
        {"cue": "c01", "head": "戻る", "lines": ["一つ"]})
    write(project / "video.yaml", video)

    result = run_engine("scriptcheck.py", "--project", str(project))
    assert result.returncode == 1
    assert "台本順で増えない" in result.stdout


def test_too_many_detail_lines_fails(run_engine, tmp_path):
    project = make_research_project(tmp_path)
    video = yaml.safe_load((project / "video.yaml").read_text(encoding="utf-8"))
    video["chapters"]["c01"]["details"][0]["lines"] = ["一", "二", "三", "四", "五"]
    write(project / "video.yaml", video)

    result = run_engine("scriptcheck.py", "--project", str(project))
    assert result.returncode == 1
    assert "4 項目まで" in result.stdout
