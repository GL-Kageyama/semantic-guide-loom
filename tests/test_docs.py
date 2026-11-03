"""文書の索引 — README の「ドキュメント」表と docs/ の実物がずれない。

- README と docs/ の相対リンクは、必ず実在する先を指す
- docs/ の各ファイルは README から引かれている（書き足して索引を忘れない）
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def targets(path: Path):
    for raw in LINK.findall(path.read_text(encoding="utf-8")):
        target = raw.split("#", 1)[0].strip()
        if not target or "://" in target or target.startswith("mailto:"):
            continue
        yield target


def test_relative_links_exist():
    broken = []
    for path in [REPO / "README.md", *sorted((REPO / "docs").glob("*.md"))]:
        for target in targets(path):
            if not (path.parent / target).exists():
                broken.append(f"{path.relative_to(REPO)} -> {target}")
    assert broken == [], "\n".join(broken)


def test_every_doc_is_indexed_from_readme():
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    linked = {t.split("#", 1)[0] for t in targets(REPO / "README.md")}
    missing = sorted(p.name for p in (REPO / "docs").glob("*.md")
                     if f"docs/{p.name}" not in linked and p.name not in readme)
    assert missing == [], f"README のドキュメント表に無い: {missing}"
