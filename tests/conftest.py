"""pytest の共通の足場。

engine/ の道具はスクリプトとして走る（`python engine/xxx.py`）。テストも同じ入口を
subprocess で叩く——**関数ではなく、実際に使う道を試す**ため。描画と YAML の依存は
venv（`$HOME/sonic-loom-spike/venv_tsukasa`）にしか無いので、そこを既定にする。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
VENV_PY = Path.home() / "sonic-loom-spike" / "venv_tsukasa" / "bin" / "python"


@pytest.fixture(scope="session")
def repo() -> Path:
    return REPO


@pytest.fixture(scope="session")
def python() -> str:
    """Pillow・numpy・PyYAML の入った python。venv が無ければいまの python。"""
    return str(VENV_PY) if VENV_PY.exists() else sys.executable


@pytest.fixture(scope="session")
def run_engine(python):
    """`python engine/<script> ...` を走らせて CompletedProcess を返す。"""

    def run(script: str, *args: str):
        return subprocess.run(
            [python, str(REPO / "engine" / script), *args],
            cwd=str(REPO),
            capture_output=True,
            text=True,
        )

    return run


@pytest.fixture(scope="session")
def template_lead(repo):
    """型が持つ `timing.chapter_lead`（timeline の章の start を決める）。"""

    def read(name: str = "dialogue-bust") -> float:
        import yaml

        path = repo / "references" / "templates" / name / "template.yaml"
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return float((doc.get("timing") or {}).get("chapter_lead", 1.6))

    return read
