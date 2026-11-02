#!/usr/bin/env python3
"""人物のデータを、確かめ・要約し・既存台本から測る。

3 つのファイルを突き合わせる。

    characters/<cast>.cast.yaml        絵の側（誰が画面に居るか）
    characters/<cast>.persona.yaml     二人（以上）の関係
    characters/<id>.character.yaml     1 人ぶんの人物造形

旧形式（persona.yaml に `characters[]` を埋め込んだもの）も読む。
新しい形では、cast の id ごとに 1 枚の人物票を要求する。

  <venv> engine/persona.py check   --cast mirai-mirabo
  <venv> engine/persona.py brief   --cast mirai-mirabo
  <venv> engine/persona.py brief   --cast mirai-mirabo --character mirai
  <venv> engine/persona.py analyze --project projects/black-swan-ai
  <venv> engine/persona.py analyze --project projects/black-swan-ai --json

設計上の約束:
- 固有名はコードに書かない。id は cast.yaml / persona.yaml / script.yaml から読む。
- 声の語彙は semantic-audio-loom の scene.schema.json から読む。写さない。
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

import characters as C
import sal_enums

REPO = Path(__file__).resolve().parent.parent
RUBY = re.compile(r"([^\s《》]+)《([^》]+)》")

# 人物票の欄 → SAL の語彙。`voice` は SAL の `emotion` を指す。
ENUM_OF = {
    "voice": "emotion",
    "speed": "speed",
    "volume": "volume",
    "delivery": "delivery",
    "intensity": "intensity",
}

RICH = ("name", "concept", "role", "wants", "fears", "contradiction", "stance")


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


def _enums() -> dict[str, set[str]]:
    return sal_enums.load()


def _check_beat(cid: str, beat: str, spec: dict, faces: set[str],
                enums: dict[str, set[str]], where: str) -> int:
    bad = 0
    if not isinstance(spec, dict):
        print(f"{where}: {cid}: {beat}: 型が辞書でない")
        return 1
    face = spec.get("face")
    if not face:
        print(f"{where}: {cid}: {beat}: face が空")
        bad += 1
    elif face not in faces:
        print(f"{where}: {cid}: {beat}: face {face!r} が cast の expressions に無い")
        bad += 1
    elif face.startswith("blink_"):
        print(f"{where}: {cid}: {beat}: face {face!r} はまばたき（使わない）")
        bad += 1
    for key, enum_key in ENUM_OF.items():
        value = spec.get(key)
        if not isinstance(value, str) or not value:
            continue
        allowed = enums.get(enum_key)
        if allowed and value not in allowed:
            print(f"{where}: {cid}: {beat}: {key} {value!r} が SAL の {enum_key} に無い")
            bad += 1
    return bad


def _check_new_sheet(cid: str, sheet: dict, cast: dict,
                     enums: dict[str, set[str]], where: str) -> int:
    bad = 0
    if not sheet.get("id"):
        print(f"{where}: id が空")
        bad += 1
    elif sheet["id"] != cid:
        print(f"{where}: id {sheet['id']!r} が cast の {cid!r} と違う")
        bad += 1

    for key in RICH:
        if not sheet.get(key):
            print(f"{where}: {cid}: {key} が空")
            bad += 1

    speech = sheet.get("speech") or {}
    if not speech.get("register"):
        print(f"{where}: {cid}: speech.register が空")
        bad += 1
    if not speech.get("length"):
        print(f"{where}: {cid}: speech.length が空（一文の長さの目安）")
        bad += 1

    emotions = sheet.get("emotions") or {}
    if not isinstance(emotions, dict) or len(emotions) < 6:
        print(f"{where}: {cid}: emotions は 6 つ以上（いま {len(emotions)}）")
        bad += 1
    faces = C.expressions(cast, cid)
    if not faces:
        print(f"{where}: {cid}: cast に expressions が無い")
        bad += 1
    for beat, spec in emotions.items():
        bad += _check_beat(cid, beat, spec, faces, enums, where)

    samples = sheet.get("samples") or []
    if not isinstance(samples, list):
        print(f"{where}: {cid}: samples が配列でない")
        bad += 1
        samples = []
    for i, sample in enumerate(samples, 1):
        if not isinstance(sample, dict):
            print(f"{where}: {cid}: samples[{i}] が辞書でない")
            bad += 1
            continue
        beat = sample.get("beat")
        if beat not in emotions:
            print(f"{where}: {cid}: samples[{i}]: beat {beat!r} が emotions に無い")
            bad += 1
        if not sample.get("line"):
            print(f"{where}: {cid}: samples[{i}]: line が空")
            bad += 1

    rel = sheet.get("relationship") or {}
    to = rel.get("to")
    if not to:
        print(f"{where}: {cid}: relationship.to が空")
        bad += 1
    elif to == cid:
        print(f"{where}: {cid}: relationship.to が自分自身")
        bad += 1
    return bad


def _check_legacy_sheet(cid: str, sheet: dict, where: str) -> int:
    bad = 0
    for key in ("name", "role", "speech"):
        if not sheet.get(key):
            print(f"{where}: {cid}: {key} が空")
            bad += 1
    if not (sheet.get("speech") or {}).get("register"):
        print(f"{where}: {cid}: speech.register が空")
        bad += 1
    return bad


def check(args) -> int:
    name = cast_name(args)
    cast = C.load_cast(name)
    persona = C.load_persona(name)
    cast_path = C.cast_path(name)
    persona_path = C.persona_path(name)
    cast_ids = C.cast_ids(cast)
    persona_ids = list(C.legacy_by_id(persona))
    bad = 0

    if not cast_ids:
        print(f"{cast_path.name}: characters が空")
        bad += 1
    if len(cast_ids) != len(set(cast_ids)):
        print(f"{cast_path.name}: id が重複している")
        bad += 1
    if len(persona_ids) != len(set(persona_ids)):
        print(f"{persona_path.name}: characters[] の id が重複している")
        bad += 1

    pair = persona.get("pair") or {}
    if not pair.get("engine"):
        print(f"{persona_path.name}: pair.engine が空")
        bad += 1
    if not pair.get("rule"):
        print(f"{persona_path.name}: pair.rule が空")
        bad += 1
    for i, dyn in enumerate(pair.get("dynamics") or [], 1):
        between = dyn.get("between") or []
        if not between:
            print(f"{persona_path.name}: pair.dynamics[{i}].between が空")
            bad += 1
            continue
        for cid in between:
            if cid not in cast_ids:
                print(f"{persona_path.name}: pair.dynamics[{i}]: {cid!r} が cast に無い")
                bad += 1
        if not (dyn.get("engine") or dyn.get("rule")):
            print(f"{persona_path.name}: pair.dynamics[{i}]: engine も rule も空")
            bad += 1

    # 旧形式の id が cast に無いものは、名前の取り違えとして落とす。
    for cid in sorted(set(persona_ids) - set(cast_ids)):
        print(f"{persona_path.name}: characters[] の id {cid!r} が cast に無い")
        bad += 1

    enums = _enums()
    if not enums:
        print("  ⚠ SAL の語彙が読めない（SAL= で場所を指定）。語彙の検査は飛ばす")
    for cid in cast_ids:
        path = C.character_path(cid)
        sheet = C.sheet_for_cast(name, cid, persona)
        if sheet is None:
            print(f"{path.name} が無い（cast の {cid!r} の人物票）")
            bad += 1
            continue
        if path.exists():
            bad += _check_new_sheet(cid, sheet, cast, enums, path.name)
        else:
            print(f"  ⚠ {cid}: 旧形式（persona.yaml の characters[]）。"
                  f"新規は {path.name} に分ける")
            bad += _check_legacy_sheet(cid, sheet, persona_path.name)

    if not bad:
        print(f"ok {cast_path.name} / {persona_path.name}（{len(cast_ids)} 人）")
    return 1 if bad else 0


def _line(label: str, value) -> None:
    if value:
        print(f"- {label}: {value}")


def _brief_sheet(sheet: dict, indent: str = "## ") -> None:
    cid = sheet.get("id") or "?"
    title = sheet.get("name") or cid
    print(f"\n{indent}{title}（{cid}）")
    _line("一行", sheet.get("concept"))
    _line("役割", sheet.get("role"))
    _line("来歴", sheet.get("background"))
    _line("欲しいもの", sheet.get("wants"))
    _line("怖いもの", sheet.get("fears"))
    _line("噛み合わない所", sheet.get("contradiction"))
    _line("構え", sheet.get("stance"))
    if sheet.get("habits"):
        print(f"- 癖: {' / '.join(sheet['habits'])}")
    humor = sheet.get("humor") or {}
    if humor.get("what") or humor.get("how"):
        print(f"- 笑い: {humor.get('what', '—')} → {humor.get('how', '—')}")

    speech = sheet.get("speech") or {}
    bits = [speech.get(k) for k in ("register", "length", "tempo") if speech.get(k)]
    if bits:
        print(f"- 話し方: {' ／ '.join(bits)}")
    if speech.get("tics"):
        print(f"- 口癖: {' / '.join(speech['tics'])}")
    if speech.get("avoids"):
        print(f"- 避ける: {' / '.join(speech['avoids'])}")
    if sheet.get("moves"):
        print(f"- 手: {' / '.join(sheet['moves'])}")
    _line("弧", sheet.get("arc"))

    rel = sheet.get("relationship") or {}
    if rel.get("to"):
        print(f"- 関係: {rel['to']} — {rel.get('line', '')}")

    emotions = sheet.get("emotions") or {}
    if emotions:
        print("\n| beat | 顔 | 声 | 速さ | 量 | 漏れ・隠す |")
        print("| --- | --- | --- | --- | --- | --- |")
        for beat, spec in emotions.items():
            if not isinstance(spec, dict):
                continue
            leak = spec.get("tell") or spec.get("withhold") or "—"
            print(f"| {beat} | {spec.get('face', '—')} | {spec.get('voice', '—')} | "
                  f"{spec.get('speed', '—')} | {spec.get('volume', '—')} | {leak} |")

    samples = sheet.get("samples") or []
    if samples:
        print("\n見本:")
        for sample in samples:
            print(f"- [{sample.get('beat')}] {sample.get('line')}")


def brief(args) -> int:
    name = cast_name(args)
    cast = C.load_cast(name)
    persona = C.load_persona(name)

    print(f"# {name}")
    if persona.get("description"):
        print(persona["description"])
    pair = persona.get("pair") or {}
    if pair.get("engine"):
        print(f"\n掛け合い: {pair['engine']}")
    if pair.get("rule"):
        print(f"約束: {pair['rule']}")
    for dyn in pair.get("dynamics") or []:
        between = " ⇄ ".join(dyn.get("between") or [])
        if between:
            print(f"\n関係 {between}")
        _line("仕組み", dyn.get("engine"))
        _line("約束", dyn.get("rule"))
        _line("こじれたら", dyn.get("escalation"))

    bad = 0
    for cid in C.cast_ids(cast):
        if args.character and cid != args.character:
            continue
        sheet = C.sheet_for_cast(name, cid, persona)
        if sheet is None:
            print(f"\n## {cid}\n（人物票が無い: characters/{cid}.character.yaml）")
            bad += 1
            continue
        _brief_sheet(sheet)

    if args.character and args.character not in C.cast_ids(cast):
        print(f"cast に {args.character!r} が居ない")
        bad += 1
    return 1 if bad else 0


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
    ap = argparse.ArgumentParser(description="人物のデータを確かめ・要約し・既存台本から測る。")
    sub = ap.add_subparsers(dest="cmd", required=True)

    for cmd, help_text in (("check", "cast・関係・人物票の id と必須欄・語彙を見る"),
                           ("brief", "台本書きに渡す人物票を出す")):
        p = sub.add_parser(cmd, help=help_text)
        p.add_argument("--cast", default="", help="characters/<name>.cast.yaml の name")
        p.add_argument("--project", default="", help="video.yaml の cast を使う場合の作品")
        if cmd == "brief":
            p.add_argument("--character", default="", help="1 人だけ出す（id）")

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
