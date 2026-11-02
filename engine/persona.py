#!/usr/bin/env python3
"""言葉の側のキャスト（persona.yaml）を、確かめ・要約し・既存台本から測る。

cast.yaml は「画面の誰か」だけを持つ。persona.yaml は「どう話すか」を持つ。
この道具はその二つを突き合わせ、台本を書く側（guide-cast / guide-script）に
渡す短い人物票と、既存台本から抽出した癖の実測を出す。

  <venv> engine/persona.py check   --cast mirai-mirabo
  <venv> engine/persona.py brief   --cast mirai-mirabo
  <venv> engine/persona.py analyze --project projects/black-swan-ai
  <venv> engine/persona.py analyze --project projects/black-swan-ai --json

設計上の約束:
- 固有名はコードに書かない。id は cast.yaml / persona.yaml / script.yaml から読む。
- analyze は表示文（video.yaml の display、無ければ script.yaml の line）を読む。
  読みのために開いた kana ではなく、視聴者が見ている文を数えるため。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
RUBY = re.compile(r"([^\s《》]+)《([^》]+)》")


def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def strip_ruby(text: str) -> str:
    """`漢字《かな》` から表示文だけを残す。"""
    return RUBY.sub(r"\1", text or "")


def cast_name(args) -> str:
    if args.cast:
        return args.cast
    if args.project:
        video = load_yaml(Path(args.project) / "video.yaml")
        name = video.get("cast") or ""
        if name:
            return name
    raise SystemExit("キャスト名が決まらない（--cast か、cast を名乗る video.yaml のある --project）")


def load_pair(name: str) -> tuple[dict, dict, Path, Path]:
    cast_path = REPO / "characters" / f"{name}.cast.yaml"
    persona_path = REPO / "characters" / f"{name}.persona.yaml"
    if not cast_path.exists():
        raise SystemExit(f"cast が無い: {cast_path}")
    if not persona_path.exists():
        raise SystemExit(f"persona が無い: {persona_path}")
    return load_yaml(cast_path), load_yaml(persona_path), cast_path, persona_path


def check(args) -> int:
    name = cast_name(args)
    cast, persona, cast_path, persona_path = load_pair(name)
    cast_ids = [c.get("id") for c in cast.get("characters", []) if c.get("id")]
    persona_ids = [c.get("id") for c in persona.get("characters", []) if c.get("id")]
    bad = 0

    if len(cast_ids) != len(set(cast_ids)):
        print(f"{cast_path.name}: id が重複している")
        bad += 1
    if len(persona_ids) != len(set(persona_ids)):
        print(f"{persona_path.name}: id が重複している")
        bad += 1

    for cid in sorted(set(cast_ids) - set(persona_ids)):
        print(f"{persona_path.name}: cast の id {cid!r} の persona が無い")
        bad += 1
    for cid in sorted(set(persona_ids) - set(cast_ids)):
        print(f"{persona_path.name}: persona の id {cid!r} が cast に無い")
        bad += 1

    for c in persona.get("characters", []):
        cid = c.get("id") or "?"
        for key in ("name", "role", "speech"):
            if not c.get(key):
                print(f"{persona_path.name}: {cid}: {key} が空")
                bad += 1
        speech = c.get("speech") or {}
        if not speech.get("register"):
            print(f"{persona_path.name}: {cid}: speech.register が空")
            bad += 1

    if not bad:
        print(f"ok {cast_path.name} / {persona_path.name}（{len(cast_ids)} 人）")
    return 1 if bad else 0


def brief(args) -> int:
    name = cast_name(args)
    _, persona, _, _ = load_pair(name)
    print(f"# {name}")
    desc = persona.get("description")
    if desc:
        print(desc)
    pair = persona.get("pair") or {}
    if pair.get("engine"):
        print(f"\n掛け合い: {pair['engine']}")
    if pair.get("rule"):
        print(f"約束: {pair['rule']}")
    for c in persona.get("characters", []):
        print(f"\n## {c.get('name') or c.get('id')}（{c.get('id')}）")
        for key, label in (("role", "役割"), ("wants", "欲しいもの"),
                           ("fears", "怖いもの"), ("stance", "構え")):
            if c.get(key):
                print(f"- {label}: {c[key]}")
        speech = c.get("speech") or {}
        if speech.get("register"):
            print(f"- 話し方: {speech['register']}")
        if speech.get("length"):
            print(f"- 長さ: {speech['length']}")
        if speech.get("tics"):
            print(f"- 癖: {' / '.join(speech['tics'])}")
        if speech.get("avoids"):
            print(f"- 避ける: {' / '.join(speech['avoids'])}")
        if c.get("moves"):
            print(f"- 手: {' / '.join(c['moves'])}")
        if c.get("arc"):
            print(f"- 弧: {c['arc']}")
    return 0


def _endings(texts: list[str], limit: int = 6) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for text in texts:
        for part in re.split(r"[。！？\n]+", text):
            part = part.strip()
            if len(part) >= 2:
                counter[part[-2:]] += 1
    return counter.most_common(limit)


def analyze(args) -> int:
    project = Path(args.project)
    script = load_yaml(project / "script.yaml")
    video = load_yaml(project / "video.yaml") if (project / "video.yaml").exists() else {}
    display = video.get("display") or {}
    rows: dict[str, dict] = {}

    for cue in script.get("cues", []):
        cid = cue.get("character") or "?"
        text = strip_ruby(display.get(cue.get("name"), cue.get("line", "")))
        row = rows.setdefault(cid, {
            "cues": 0, "chars": 0, "max": 0, "texts": [],
            "questions": 0, "exclamations": 0, "ellipsis": 0, "percent": 0,
        })
        row["cues"] += 1
        row["chars"] += len(text)
        row["max"] = max(row["max"], len(text))
        row["texts"].append(text)
        row["questions"] += text.count("？") + text.count("?")
        row["exclamations"] += text.count("！") + text.count("!")
        row["ellipsis"] += text.count("……")
        row["percent"] += text.count("%") + text.count("％")

    out = {}
    for cid, row in rows.items():
        cues = max(1, row["cues"])
        out[cid] = {
            "cues": row["cues"],
            "avg_chars": round(row["chars"] / cues, 1),
            "max_chars": row["max"],
            "question_rate": round(row["questions"] / cues, 3),
            "exclamation_rate": round(row["exclamations"] / cues, 3),
            "ellipsis_rate": round(row["ellipsis"] / cues, 3),
            "percent_rate": round(row["percent"] / cues, 3),
            "endings": _endings(row["texts"]),
        }

    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    print(f"# {project.name} の話し方（表示文から）")
    print("\n| 人物 | cue | 平均字数 | 最長 | 疑問文 | ！ | …… | % | よく出る文末 |")
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
    for cid, r in out.items():
        endings = " / ".join(f"{e}({n})" for e, n in r["endings"][:4]) or "—"
        print(f"| {cid} | {r['cues']} | {r['avg_chars']} | {r['max_chars']} | "
              f"{r['question_rate']:.0%} | {r['exclamation_rate']:.0%} | "
              f"{r['ellipsis_rate']:.0%} | {r['percent_rate']:.0%} | {endings} |")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="persona.yaml を確かめ・要約し・既存台本から測る。")
    sub = ap.add_subparsers(dest="cmd", required=True)

    for cmd, help_text in (("check", "cast と persona の id・必須欄を見る"),
                           ("brief", "台本書きに渡す人物票を出す")):
        p = sub.add_parser(cmd, help=help_text)
        p.add_argument("--cast", default="", help="characters/<name>.cast.yaml の name")
        p.add_argument("--project", default="", help="video.yaml の cast を使う場合の作品")

    p = sub.add_parser("analyze", help="既存 script.yaml から人物ごとの癖を測る")
    p.add_argument("--project", required=True)
    p.add_argument("--json", action="store_true")

    args = ap.parse_args()
    if args.cmd == "check":
        return check(args)
    if args.cmd == "brief":
        return brief(args)
    return analyze(args)


if __name__ == "__main__":
    sys.exit(main())
