#!/usr/bin/env python3
"""演技の欄を検査し、台本の感情の振れ幅を測る。

見るのは 2 つ。

1. **参照切れ。** emotion / speed / volume / delivery / intensity が SAL の語彙か。
   face がキャストの expressions に実在するか。beat が人物票の emotions にあるか。
   react の相手がキャストに居るか。
2. **網羅と単調さ。** beat と表情の網羅率、人物ごとの表情の種類、聞き手の反応、
   速度の分布、間の広がり、同じ速度・同じ表情の最長連続。

語彙の正本は semantic-audio-loom の `schemas/scene.schema.json`。写さない。
計測は `review/acting/<版>.yaml` に置く（`review/reports/` には置かない。
`review.py` が評価者の JSON と数えてしまうため）。

  <venv> engine/acting.py audit   --project projects/<作品> [--strict] [--json]
  <venv> engine/acting.py report  --project projects/<作品> --out review/acting/v4.yaml \
                                  [--script <別の script.yaml>] [--version v4]
  <venv> engine/acting.py compare --before review/acting/v1.yaml --after review/acting/v4.yaml

終了コード: 参照切れがあれば 1。警告は既定では 0（--strict なら 1）。
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

import yaml

import characters as C
import sal_enums

REPO = Path(__file__).resolve().parent.parent
RUBY = re.compile(r"([^\s《》]+)《([^》]+)》")

VOICE_ENUMS = {
    "emotion": "emotion",
    "speed": "speed",
    "volume": "volume",
    "delivery": "delivery",
    "intensity": "intensity",
}

# 完了条件（計画）。警告の閾値であって、判定そのものは人がする。
BEAT_RATE = 0.90
FACE_RATE = 0.90
REACT_RATE = 0.60
MIN_FACES = 5
MIN_SPEEDS = 4
MAX_RUN_SHARE = 0.25
MARKS_MIN, MARKS_MAX = 8, 15


def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def strip_ruby(text: str) -> str:
    return RUBY.sub(r"\1", text or "")


def rate(n: int, d: int) -> float:
    return round(n / d, 3) if d else 0.0


def _cast(name: str) -> tuple[dict, dict[str, set[str]], dict[str, dict]]:
    path = REPO / "characters" / f"{name}.cast.yaml"
    if not path.exists():
        return {}, {}, {}
    doc = load_yaml(path)
    faces = {c.get("id"): set(c.get("expressions") or [])
             for c in doc.get("characters", []) if c.get("id")}
    sheets = {cid: C.sheet_for_cast(name, cid) for cid in faces}
    return doc, faces, sheets


def _resolved_face(cue: dict, cid: str, faces: set[str], spec: dict,
                   sheet: dict | None = None) -> tuple[str, bool]:
    """(表情, 明示か)。明示 face → beat → emotion。無ければ ("", False)。

    既定の neutral は数えない（解決しなかった cue と区別するため）。
    規則は characters.resolve_face に 1 つだけ置く。
    """
    return C.resolve_face(cue, faces, spec, sheet)


def _longest_run(values: list[str]) -> tuple[str, int]:
    best, best_n = "", 0
    cur, cur_n = "", 0
    for value in values:
        if value and value == cur:
            cur_n += 1
        else:
            cur, cur_n = value, 1 if value else 0
        if cur_n > best_n:
            best, best_n = cur, cur_n
    return best, best_n


def collect(project: Path, script_path: Path | None = None,
            cast_name: str = "") -> dict:
    script = load_yaml(script_path or (project / "script.yaml"))
    video = load_yaml(project / "video.yaml") if (project / "video.yaml").exists() else {}
    cast_name = cast_name or video.get("cast") or ""
    display = video.get("display") or {}
    cast_doc, faces, sheets = _cast(cast_name) if cast_name else ({}, {}, {})
    spec_by_id = {c.get("id"): c for c in cast_doc.get("characters", []) if c.get("id")}
    ids = set(faces)
    enums = sal_enums.load()

    cues = script.get("cues") or []
    errors: list[str] = []
    warnings: list[str] = []

    speaking = [c for c in cues if c.get("character")]
    beat_n = face_n = face_explicit_n = emotion_n = 0
    speeds: list[str] = []
    speed_run_values: list[str] = []
    pauses: list[float] = []
    face_run_values: list[str] = []
    react_face_n = 0
    opportunities = 0
    mark_n = 0
    mark_seq: list[tuple[str, str]] = []
    per: dict[str, dict] = {}

    for cue in cues:
        name = cue.get("name") or "?"
        cid = cue.get("character") or ""

        if cid and cid not in ids:
            errors.append(f"{name}: character {cid!r} が cast に無い")

        for key, enum_key in VOICE_ENUMS.items():
            value = cue.get(key)
            if value is None or value == "":
                continue
            if not isinstance(value, str):
                errors.append(f"{name}: {key} が文字列でない")
                continue
            allowed = enums.get(enum_key)
            if allowed and value not in allowed:
                errors.append(f"{name}: {key} {value!r} が SAL の {enum_key} に無い")

        face = cue.get("face")
        if face:
            if not isinstance(face, str):
                errors.append(f"{name}: face が文字列でない")
            else:
                if face.startswith("blink_"):
                    errors.append(f"{name}: face {face!r} はまばたき（使わない）")
                if cid in faces and face not in faces[cid]:
                    errors.append(f"{name}: face {face!r} が {cid} の expressions に無い")

        beat = cue.get("beat")
        if beat:
            sheet = sheets.get(cid)
            if sheet is None:
                warnings.append(f"{name}: beat {beat!r} を検査できない（{cid} の人物票が無い）")
            elif beat not in (sheet.get("emotions") or {}):
                errors.append(f"{name}: beat {beat!r} が {cid} の emotions に無い")

        pb = cue.get("pause_before")
        if pb is not None:
            if not isinstance(pb, (int, float)) or isinstance(pb, bool):
                errors.append(f"{name}: pause_before が数値でない")
            elif pb < 0:
                errors.append(f"{name}: pause_before が負（{pb}）")
            elif pb > 5:
                warnings.append(f"{name}: pause_before が {pb} 秒（長すぎないか）")
            else:
                pauses.append(float(pb))

        if cid:
            row = per.setdefault(cid, {
                "cues": 0, "chars": 0, "questions": 0, "faces": Counter(),
                "beats": Counter(), "speeds": Counter(), "marks": 0,
            })
            text = strip_ruby(display.get(name) or cue.get("line", ""))
            row["cues"] += 1
            row["chars"] += len(text)
            row["questions"] += text.count("？") + text.count("?")
            if beat:
                row["beats"][beat] += 1
                beat_n += 1
            emotion = cue.get("emotion") or ""
            if emotion:
                emotion_n += 1
            resolved, explicit = _resolved_face(cue, cid, faces.get(cid, set()),
                                                spec_by_id.get(cid) or {},
                                                sheets.get(cid))
            if resolved:
                face_n += 1
                row["faces"][resolved] += 1
                if explicit:
                    face_explicit_n += 1
            face_run_values.append(resolved)
            speed = cue.get("speed") or ""
            if speed:
                speeds.append(speed)
                row["speeds"][speed] += 1
            speed_run_values.append(speed)

        react = cue.get("react")
        if react is not None:
            if not isinstance(react, dict):
                errors.append(f"{name}: react が辞書でない")
            else:
                for rid, entry in react.items():
                    if rid not in ids:
                        errors.append(f"{name}: react の {rid!r} が cast に無い")
                        continue
                    if not isinstance(entry, dict):
                        errors.append(f"{name}: react.{rid} が辞書でない")
                        continue
                    rface = entry.get("face")
                    rbeat = entry.get("beat")
                    mark = entry.get("mark")
                    if not rface and not rbeat and not mark:
                        errors.append(f"{name}: react.{rid} に顔も記号も無い")
                    if rface:
                        if not isinstance(rface, str):
                            errors.append(f"{name}: react.{rid}.face が文字列でない")
                        elif rface.startswith("blink_"):
                            errors.append(f"{name}: react.{rid}.face {rface!r} はまばたき")
                        elif rface not in faces.get(rid, set()):
                            errors.append(f"{name}: react.{rid}.face {rface!r} が "
                                          f"{rid} の expressions に無い")
                    if rbeat:
                        sheet = sheets.get(rid)
                        if sheet is not None and rbeat not in (sheet.get("emotions") or {}):
                            errors.append(f"{name}: react.{rid}.beat {rbeat!r} が "
                                          f"{rid} の emotions に無い")
                    # 顔は明示 face か beat から解決する（話し手と同じ規則）。
                    rresolved, _ = C.resolve_face(
                        {"face": rface if isinstance(rface, str) else "",
                         "beat": rbeat if isinstance(rbeat, str) else ""},
                        faces.get(rid, set()), spec_by_id.get(rid) or {},
                        sheets.get(rid))
                    if rresolved:
                        react_face_n += 1
                    if mark:
                        if not isinstance(mark, str):
                            errors.append(f"{name}: react.{rid}.mark が文字列でない")
                        elif len(mark) > 3:
                            errors.append(f"{name}: react.{rid}.mark が {len(mark)} 字（3 字まで）")
                        else:
                            mark_n += 1
                            mark_seq.append((name, rid))
                            if rid in per:
                                per[rid]["marks"] += 1

    # 聞き手の反応の機会：発話 cue × 他のキャスト。
    for cue in speaking:
        opportunities += max(0, len(ids) - 1)

    for cid, row in per.items():
        n = max(1, row["cues"])
        row["avg_chars"] = round(row["chars"] / n, 1)
        row["question_rate"] = rate(row["questions"], n)
        row["distinct_faces"] = len(row["faces"])
        row["faces"] = dict(row["faces"].most_common())
        row["beats"] = dict(row["beats"].most_common())
        row["speeds"] = dict(row["speeds"].most_common())

    _, face_run = _longest_run(face_run_values)
    _, speed_run = _longest_run(speed_run_values)
    same_mark = 0
    prev = ""
    for _, cid in mark_seq:
        if cid == prev:
            same_mark += 1
        prev = cid

    total = max(1, len(speaking))
    metrics = {
        "cues": len(cues),
        "speaking": len(speaking),
        "beat": {"count": beat_n, "rate": rate(beat_n, total)},
        "face": {"count": face_n, "rate": rate(face_n, total),
                 "explicit": face_explicit_n,
                 "explicit_rate": rate(face_explicit_n, total)},
        "emotion": {"count": emotion_n, "rate": rate(emotion_n, total)},
        "speed": {"distinct": len(set(speeds)),
                  "values": dict(Counter(speeds).most_common()),
                  "longest_run": speed_run,
                  "longest_share": rate(speed_run, total)},
        "face_longest_run": face_run,
        "face_longest_share": rate(face_run, total),
        "pause_before": {
            "count": len(pauses),
            "min": round(min(pauses), 3) if pauses else None,
            "max": round(max(pauses), 3) if pauses else None,
            "median": round(statistics.median(pauses), 3) if pauses else None,
        },
        "react": {"face_count": react_face_n, "opportunities": opportunities,
                  "face_rate": rate(react_face_n, opportunities),
                  "mark_count": mark_n, "back_to_back": same_mark},
        "characters": per,
    }

    # 完了条件に照らした警告。判定はしない。
    if speaking and metrics["beat"]["rate"] < BEAT_RATE:
        warnings.append(f"beat の網羅 {metrics['beat']['rate']:.0%}（目標 {BEAT_RATE:.0%}）")
    if speaking and metrics["face"]["rate"] < FACE_RATE:
        warnings.append(f"face の解決 {metrics['face']['rate']:.0%}"
                        f"（目標 {FACE_RATE:.0%}／明示 {metrics['face']['explicit_rate']:.0%}）")
    for cid, row in per.items():
        if row["cues"] and row["distinct_faces"] < MIN_FACES:
            warnings.append(f"{cid}: 表情が {row['distinct_faces']} 種類"
                            f"（目標 {MIN_FACES} 種類以上）")
    if len(ids) > 1 and opportunities and metrics["react"]["face_rate"] < REACT_RATE:
        warnings.append(f"聞き手の反応（顔）{metrics['react']['face_rate']:.0%}"
                        f"（目標 {REACT_RATE:.0%}）")
    if speaking and metrics["speed"]["distinct"] < MIN_SPEEDS:
        warnings.append(f"速度が {metrics['speed']['distinct']} 語"
                        f"（目標 {MIN_SPEEDS} 語以上）")
    if speaking and metrics["speed"]["longest_share"] >= MAX_RUN_SHARE:
        warnings.append(f"同じ速度の最長連続 {metrics['speed']['longest_share']:.0%}"
                        f"（目標 {MAX_RUN_SHARE:.0%} 未満）")
    if pauses and (min(pauses) > 0.5 or max(pauses) < 1.0):
        warnings.append("間（pause_before）の広がりが小さい"
                        f"（{min(pauses):.2f}〜{max(pauses):.2f} 秒）")
    if mark_n and not (MARKS_MIN <= mark_n <= MARKS_MAX):
        warnings.append(f"記号が {mark_n} か所（目標 {MARKS_MIN}〜{MARKS_MAX} か所）")
    if same_mark:
        warnings.append(f"同じ人物に記号が続けて {same_mark} 回")

    return {
        "project": str(project),
        "script": str(script_path or (project / "script.yaml")),
        "cast": cast_name,
        "metrics": metrics,
        "errors": errors,
        "warnings": warnings,
    }


def _print_audit(data: dict, strict: bool) -> int:
    m = data["metrics"]
    print(f"{m['cues']} cue / {m['speaking']} 発話（cast: {data['cast'] or '—'}）")
    print(f"beat       {m['beat']['count']:>4}/{m['speaking']:<4} {m['beat']['rate']:.0%}")
    print(f"face       {m['face']['count']:>4}/{m['speaking']:<4} {m['face']['rate']:.0%}"
          f"（明示 {m['face']['explicit']} / {m['face']['explicit_rate']:.0%}）")
    print(f"聞き手の顔 {m['react']['face_count']:>4}/{m['react']['opportunities']:<4}"
          f" {m['react']['face_rate']:.0%}")
    print(f"記号       {m['react']['mark_count']:>4} か所")
    sp = m["speed"]
    print(f"速度       {sp['distinct']} 語 / 最長連続 {sp['longest_run']}"
          f"（{sp['longest_share']:.0%}）")
    pb = m["pause_before"]
    if pb["count"]:
        print(f"間         {pb['min']}〜{pb['max']} 秒（中央 {pb['median']}）")
    else:
        print("間         なし")

    if m["characters"]:
        print("\n| 人物 | cue | 表情 | 平均字数 | 疑問文 | 記号 |")
        print("| --- | ---: | ---: | ---: | ---: | ---: |")
        for cid, row in m["characters"].items():
            print(f"| {cid} | {row['cues']} | {row['distinct_faces']} 種 | "
                  f"{row['avg_chars']} | {row['question_rate']:.0%} | {row['marks']} |")

    if data["errors"]:
        print(f"\nエラー {len(data['errors'])} 件")
        for line in data["errors"]:
            print(f"  {line}")
    if data["warnings"]:
        print(f"\n警告 {len(data['warnings'])} 件")
        for line in data["warnings"]:
            print(f"  {line}")
    if not data["errors"] and not data["warnings"]:
        print("\nok")
    return 1 if data["errors"] or (strict and data["warnings"]) else 0


def audit(args) -> int:
    project = Path(args.project)
    script = Path(args.script) if args.script else None
    data = collect(project, script, args.cast)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 1 if data["errors"] or (args.strict and data["warnings"]) else 0
    return _print_audit(data, args.strict)


def report(args) -> int:
    project = Path(args.project)
    script = Path(args.script) if args.script else None
    data = collect(project, script, args.cast)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "version": args.version or out.stem,
        "project": data["project"],
        "script": data["script"],
        "cast": data["cast"],
        "metrics": data["metrics"],
        "errors": data["errors"],
        "warnings": data["warnings"],
    }
    with open(out, "w", encoding="utf-8") as f:
        f.write("# 演技の計測。engine/acting.py report が作る。\n")
        f.write("# review/reports/ には置かない（評議会の評価者と数えてしまうため）。\n")
        yaml.safe_dump(doc, f, allow_unicode=True, sort_keys=False)
    print(f"書いた: {out}")
    if data["errors"]:
        print(f"エラー {len(data['errors'])} 件（report は残した）")
        return 1
    return 0


def _flat(doc: dict) -> dict[str, float | None]:
    m = doc.get("metrics") or {}
    chars = m.get("characters") or {}
    faces = [row.get("distinct_faces") or 0 for row in chars.values()]
    return {
        "beat": (m.get("beat") or {}).get("rate"),
        "face": (m.get("face") or {}).get("rate"),
        "react": (m.get("react") or {}).get("face_rate"),
        "marks": (m.get("react") or {}).get("mark_count"),
        "speeds": (m.get("speed") or {}).get("distinct"),
        "speed_run": (m.get("speed") or {}).get("longest_share"),
        "pause_min": (m.get("pause_before") or {}).get("min"),
        "pause_max": (m.get("pause_before") or {}).get("max"),
        "min_faces": min(faces) if faces else 0,
    }


def _fmt(key: str, value) -> str:
    if value is None:
        return "—"
    if key in ("beat", "face", "react", "speed_run"):
        return f"{value:.0%}"
    if key in ("pause_min", "pause_max"):
        return f"{value:.2f}s"
    return f"{value:g}" if isinstance(value, float) else str(value)


def compare(args) -> int:
    before = load_yaml(Path(args.before))
    after = load_yaml(Path(args.after))
    a, b = _flat(before), _flat(after)
    print(f"| 指標 | {before.get('version', 'before')} | {after.get('version', 'after')} | 差 |")
    print("| --- | ---: | ---: | ---: |")
    for key in a:
        va, vb = a[key], b[key]
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            diff = vb - va
            ds = f"{diff:+.0%}" if key in ("beat", "face", "react", "speed_run") else f"{diff:+g}"
        else:
            ds = "—"
        print(f"| {key} | {_fmt(key, va)} | {_fmt(key, vb)} | {ds} |")
    chars_before = set((before.get("metrics") or {}).get("characters") or {})
    chars_after = set((after.get("metrics") or {}).get("characters") or {})
    if chars_before != chars_after:
        print(f"\n人物が違う: {sorted(chars_before)} → {sorted(chars_after)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="演技の参照切れを見て、感情の振れ幅を測る。")
    sub = ap.add_subparsers(dest="cmd", required=True)

    for cmd, help_text in (("audit", "演技の欄を検査し、網羅と単調さを測る"),
                           ("report", "版ごとの計測を YAML に残す")):
        p = sub.add_parser(cmd, help=help_text)
        p.add_argument("--project", required=True)
        p.add_argument("--script", default="", help="別の script.yaml（旧版を測るとき）")
        p.add_argument("--cast", default="", help="video.yaml の cast を上書き")
        if cmd == "audit":
            p.add_argument("--strict", action="store_true")
            p.add_argument("--json", action="store_true")
        else:
            p.add_argument("--out", required=True)
            p.add_argument("--version", default="")

    p = sub.add_parser("compare", help="2 版の計測を並べる")
    p.add_argument("--before", required=True)
    p.add_argument("--after", required=True)

    args = ap.parse_args()
    if args.cmd == "audit":
        return audit(args)
    if args.cmd == "report":
        return report(args)
    return compare(args)


if __name__ == "__main__":
    sys.exit(main())
