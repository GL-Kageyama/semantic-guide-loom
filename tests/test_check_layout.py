"""`tools/check_layout.py` — 置き場・スキーマ・古い綴りの検査。

これが緑であることが、文書と `schemas/` の整合の基準線。
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_layout_check_passes(python, repo):
    import subprocess

    result = subprocess.run(
        [python, str(repo / "tools" / "check_layout.py")],
        cwd=str(repo), capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
