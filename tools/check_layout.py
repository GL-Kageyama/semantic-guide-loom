#!/usr/bin/env python3
"""置き場の綴りが、いまのリポジトリと合っているかを見る。

2 つを見る。

1. **古い綴りが残っていないか。** 置き場を移したとき、文書とコードのどこかに
   `works/` `casts/` `sheets/` `templates/` `out/` が残ると、clone した人が
   存在しない道を辿る。**HISTORY.md は除く**（過去の綴りを書くのが役目）。
2. **schemas/ が実物に通るか。** 欄を外していないかを、置いてある YAML で確かめる。

  <venv> tools/check_layout.py
  <venv> tools/check_layout.py --no-schema     # 綴りだけ

`jsonschema` が無い環境では 2 を飛ばす（素の python3 は持っていない）。
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# 古い綴り → いまの置き場。**前方が正しい親ディレクトリのものは当てない**
# （`references/templates/` は正しいので、`/` の直後の `templates/` は拾わない）。
# 3 つ目は「`references/` の中の文書なら相対の道として許す」か。
STALE = [
    (re.compile(r"(?<![\w-])works/"), "works/ → projects/", False),
    (re.compile(r"(?<![\w-])casts/"), "casts/ → characters/", False),
    (re.compile(r"(?<![\w/-])templates/"), "templates/ → references/templates/", True),
    (re.compile(r"(?<![\w/-])sheets/"), "sheets/ → references/sheets/", True),
    (re.compile(r"(?<![\w-])out/"), "out/ → projects/<作品>/renders/", False),
]

TEXT_SUFFIXES = {".md", ".py", ".sh", ".yaml", ".yml", ".json", ".txt"}
SKIP = {
    "HISTORY.md",              # 過去の綴りを書くのが役目
    "tools/check_layout.py",   # 検査の語そのもの
}

# `references/` の中の文書は、**同じ木の中の相対の道**（`templates/…`）を書いてよい。
# そこだけ `rel_ok` の付いた綴りを見逃す。`works/` `casts/` `out/` は見逃さない。
RELATIVE_OK_PREFIX = "references/"

# (schema, 当てる相手)
SCHEMAS = [
    ("schemas/video.schema.json", "projects/*/video.yaml"),
    ("schemas/template.schema.json", "references/templates/*/template.yaml"),
    ("schemas/cast.schema.json", "characters/*.cast.yaml"),
    ("schemas/persona.schema.json", "characters/*.persona.yaml"),
    ("schemas/character.schema.json", "characters/*.character.yaml"),
    ("schemas/reading.schema.json", "projects/*/reading.yaml"),
    ("schemas/bgm.schema.json", "projects/*/bgm.yaml"),
    ("schemas/viewer.schema.json", "projects/*/review/viewers/*/r*.json"),
]


def tracked_text_files() -> list[str]:
    out = subprocess.run(["git", "-C", str(REPO), "ls-files", "-z"],
                         check=True, capture_output=True)
    paths = [p for p in out.stdout.decode().split("\0") if p]
    return [p for p in paths
            if Path(p).suffix in TEXT_SUFFIXES and p not in SKIP]


def check_paths() -> int:
    bad = 0
    for rel in tracked_text_files():
        path = REPO / rel
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        relative_ok = rel.startswith(RELATIVE_OK_PREFIX)
        for n, line in enumerate(lines, 1):
            for pat, hint, allow_relative in STALE:
                if relative_ok and allow_relative:
                    continue
                if pat.search(line):
                    print(f"{rel}:{n}: {hint}")
                    print(f"    {line.strip()[:100]}")
                    bad += 1
    return bad


def check_schemas() -> int:
    try:
        import yaml
        from jsonschema import Draft202012Validator
    except ImportError as e:
        print(f"  (飛ばした: {e})")
        return 0
    bad = 0
    for schema_rel, pattern in SCHEMAS:
        with open(REPO / schema_rel, encoding="utf-8") as f:
            validator = Draft202012Validator(json.load(f))
        files = sorted(glob.glob(str(REPO / pattern)))
        if not files:
            print(f"  ⚠ 当てる相手が居ない: {pattern}")
            continue
        for p in files:
            with open(p, encoding="utf-8") as f:
                doc = yaml.safe_load(f)
            errs = sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
            for err in errs:
                loc = "/".join(str(x) for x in err.path) or "(根)"
                print(f"{Path(p).relative_to(REPO)}: {loc}: {err.message}")
                bad += 1
            if not errs:
                print(f"  ok {Path(p).relative_to(REPO)}")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-schema", action="store_true")
    args = ap.parse_args()

    print("== 綴り ==")
    bad = check_paths()
    if not bad:
        print("  ok 古い綴りは無い")

    if not args.no_schema:
        print("== schemas/ ==")
        bad += check_schemas()

    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
