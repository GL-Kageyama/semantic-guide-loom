#!/usr/bin/env python3
"""表示文から、声に読ませるためのかなの台本（reading.yaml）を作る。

字幕は script.yaml / video.yaml が持つ。読みは生成専用で、別に持つ。
この道具は、その下書き・監査・ビルド用の舞台づくりをする。判断はしない。

  <venv> engine/reading.py draft  --project projects/<作品>
  <venv> engine/reading.py audit  --project projects/<作品>
  <venv> engine/reading.py audit  --project projects/<作品> --phonemize --cue c001
  <venv> engine/reading.py stage  --project projects/<作品> --assets projects/<作品>/assets

draft は fugashi（unidic-lite）で漢字を開く。日付だけは表で先に直す
（四月→しがつ、七月→しちがつ、九月→くがつ、一日〜三十一日の特殊読み）。
アラビア数字・%・Latin は触らず、`needs_review` に cue 名を残す。人が決める。

stage は作品を書き換えない。build/<作品>/ に、`line` を読みへ差し替えた
script.yaml と、元の表記を `display` に補った video.yaml を置く。
"""
from __future__ import annotations

import argparse
import copy
import os
import re
import shutil
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
RUBY = re.compile(r"([^\s《》]+)《([^》]+)》")
KANJI = re.compile(r"[一-龯]")
LATIN = re.compile(r"[A-Za-zＡ-ｚ]")
DIGITS = re.compile(r"[0-9０-９]")
PERCENT = re.compile(r"[%％]")

KATA_TO_HIRA = str.maketrans({chr(c): chr(c - 0x60) for c in range(0x30A1, 0x30F7)})

DIGIT = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
MONTH = {
    1: "いちがつ", 2: "にがつ", 3: "さんがつ", 4: "しがつ", 5: "ごがつ", 6: "ろくがつ",
    7: "しちがつ", 8: "はちがつ", 9: "くがつ", 10: "じゅうがつ", 11: "じゅういちがつ",
    12: "じゅうにがつ",
}
DAY = {
    1: "ついたち", 2: "ふつか", 3: "みっか", 4: "よっか", 5: "いつか", 6: "むいか",
    7: "なのか", 8: "ようか", 9: "ここのか", 10: "とおか", 11: "じゅういちにち",
    12: "じゅうににち", 13: "じゅうさんにち", 14: "じゅうよっか", 15: "じゅうごにち",
    16: "じゅうろくにち", 17: "じゅうしちにち", 18: "じゅうはちにち", 19: "じゅうくにち",
    20: "はつか", 21: "にじゅういちにち", 22: "にじゅうににち", 23: "にじゅうさんにち",
    24: "にじゅうよっか", 25: "にじゅうごにち", 26: "にじゅうろくにち",
    27: "にじゅうしちにち", 28: "にじゅうはちにち", 29: "にじゅうくにち",
    30: "さんじゅうにち", 31: "さんじゅういちにち",
}
DATE = re.compile(r"([一二三四五六七八九十]{1,3})月([一二三四五六七八九十]{1,3})日")
DAY_ALONE = re.compile(r"([一二三四五六七八九十]{1,3})日(?![中半間分後前目])")

NEEDS_REVIEW = ("数字", "%", "Latin")


def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def strip_ruby(text: str) -> str:
    return RUBY.sub(r"\1", text or "")


def kanji_number(text: str) -> int | None:
    if not text:
        return None
    if "十" in text:
        head, _, tail = text.partition("十")
        tens = DIGIT.get(head, 1) if head else 1
        ones = DIGIT.get(tail, 0) if tail else 0
        if (head and head not in DIGIT) or (tail and tail not in DIGIT) or len(tail) > 1:
            return None
        return tens * 10 + ones
    if len(text) == 1 and text in DIGIT:
        return DIGIT[text]
    return None


def correct_dates(text: str) -> tuple[str, list[str]]:
    """月日の特殊読みを、トークン化の前に直す。直した表記を返す。"""
    fixed: list[str] = []

    def month_day(m: re.Match) -> str:
        month, day = kanji_number(m.group(1)), kanji_number(m.group(2))
        if month in MONTH and day in DAY:
            fixed.append(m.group(0))
            return MONTH[month] + DAY[day]
        return m.group(0)

    text = DATE.sub(month_day, text)

    def day_alone(m: re.Match) -> str:
        day = kanji_number(m.group(1))
        if day in DAY:
            fixed.append(m.group(0))
            return DAY[day]
        return m.group(0)

    text = DAY_ALONE.sub(day_alone, text)
    return text, fixed


def to_reading(text: str, tagger) -> tuple[str, list[str], list[str]]:
    """表示文 → 読み。戻り値は（読み, 直した月日, 要確認の理由）。"""
    text = strip_ruby(text)
    text, fixed = correct_dates(text)
    out: list[str] = []
    for word in tagger(text):
        kana = getattr(word.feature, "kana", None)
        if kana:
            out.append(kana.translate(KATA_TO_HIRA))
        else:
            out.append(word.surface)
    reading = "".join(out)

    reasons: list[str] = []
    if DIGITS.search(text):
        reasons.append("数字")
    if PERCENT.search(text):
        reasons.append("%")
    if LATIN.search(text):
        reasons.append("Latin")
    return reading, fixed, reasons


def project_cues(project: Path) -> tuple[dict, dict, dict]:
    script = load_yaml(project / "script.yaml")
    video = load_yaml(project / "video.yaml") if (project / "video.yaml").exists() else {}
    return script, video, (video.get("display") or {})


def cue_text(cue: dict, display: dict) -> str:
    return strip_ruby(display.get(cue.get("name"), cue.get("line", "")))


def draft(args) -> int:
    project = Path(args.project)
    script, _, display = project_cues(project)
    out_path = Path(args.out) if args.out else project / "reading.yaml"
    if out_path.exists() and not args.force:
        raise SystemExit(f"既にある: {out_path}（作り直すなら --force）")

    try:
        from fugashi import Tagger
    except ImportError as exc:
        raise SystemExit(f"fugashi が無い（venv を使う）: {exc}") from exc

    tagger = Tagger()
    readings: dict[str, str] = {}
    needs: list[str] = []
    dates: list[str] = []
    for cue in script.get("cues", []):
        name = cue.get("name") or ""
        if not name:
            continue
        reading, fixed, reasons = to_reading(cue_text(cue, display), tagger)
        readings[name] = reading
        if reasons:
            needs.append(name)
        if fixed:
            dates.append(f"{name}: {' / '.join(fixed)}")

    doc: dict = {"name": project.name, "readings": readings}
    if needs:
        doc["needs_review"] = needs
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# 声に読ませるための読み。字幕は script.yaml / video.yaml が持つ。\n")
        f.write("# engine/reading.py draft の下書き。数字・%・Latin は人が決める。\n")
        yaml.safe_dump(doc, f, allow_unicode=True, sort_keys=False)

    print(f"書いた: {out_path}（{len(readings)} cue、要確認 {len(needs)} cue）")
    if needs:
        print(f"  要確認: {' '.join(needs)}")
    if dates:
        print(f"  月日を直した: {len(dates)} か所")
        for line in dates[:20]:
            print(f"    {line}")
        if len(dates) > 20:
            print(f"    …ほか {len(dates) - 20} か所")
    return 0


def load_phonemize():
    tsukasa = Path(os.environ.get("TSUKASA", Path.home() / "sonic-loom-spike" / "tsukasa"))
    if not (tsukasa / "Utils" / "phonemize" / "cotlet_phon.py").exists():
        return None
    sys.path.insert(0, str(tsukasa))
    old = os.getcwd()
    os.chdir(tsukasa)
    try:
        from Utils.phonemize.cotlet_phon import phonemize
    except Exception:
        return None
    finally:
        os.chdir(old)
    return phonemize


def audit(args) -> int:
    project = Path(args.project)
    script, _, display = project_cues(project)
    reading_path = project / "reading.yaml"
    if not reading_path.exists():
        print(f"読みが無い: {reading_path}（先に draft）")
        return 1
    doc = load_yaml(reading_path)
    readings = doc.get("readings") or {}
    flagged: list[str] = []
    warnings: list[str] = []

    cue_names = [c.get("name") for c in script.get("cues", []) if c.get("name")]
    for name in cue_names:
        reading = readings.get(name)
        if not reading:
            warnings.append(f"{name}: 読みが無い")
            continue
        reasons = []
        if DIGITS.search(reading):
            reasons.append("数字")
        if PERCENT.search(reading):
            reasons.append("%")
        if LATIN.search(reading):
            reasons.append("Latin")
        if KANJI.search(reading):
            reasons.append("漢字")
        if reasons:
            warnings.append(f"{name}: 読みに{'・'.join(reasons)}が残る: {reading}")
            flagged.append(name)
    for name in sorted(set(readings) - set(cue_names)):
        warnings.append(f"{name}: script.yaml に無い cue")

    for name in cue_names:
        text = cue_text(next(c for c in script["cues"] if c.get("name") == name), display)
        if len(text) > 27:
            warnings.append(f"{name}: 字幕が {len(text)} 字（27 字超）: {text}")
    if doc.get("needs_review"):
        warnings.append(f"draft の要確認: {' '.join(doc['needs_review'])}")

    if args.phonemize:
        phonemize = load_phonemize()
        if phonemize is None:
            print("Tsukasa の phonemize が見つからない（TSUKASA で場所を指定）")
            return 1
        targets = [args.cue] if args.cue else cue_names
        for name in targets:
            reading = readings.get(name, "")
            if not reading:
                continue
            try:
                phones = phonemize(reading)
            except Exception as exc:
                phones = f"（失敗: {exc}）"
            print(f"{name}\t{reading}\t{phones}")

    if warnings:
        print(f"警告 {len(warnings)} 件（要確認 {len(flagged)} cue）")
        for line in warnings:
            print(f"  {line}")
        if args.strict:
            return 1
    else:
        print(f"ok {len(cue_names)} cue")
    return 0


def stage(args) -> int:
    project = Path(args.project)
    script, video, display = project_cues(project)
    reading_path = project / "reading.yaml"
    if not reading_path.exists():
        raise SystemExit(f"読みが無い: {reading_path}（先に draft）")
    readings = (load_yaml(reading_path).get("readings") or {})
    stage = Path(args.stage).resolve() if args.stage else REPO / "build" / project.name
    stage.mkdir(parents=True, exist_ok=True)

    new_script = copy.deepcopy(script)
    new_video = copy.deepcopy(video)
    new_display = dict(new_video.get("display") or {})
    missing: list[str] = []
    changed = 0
    for cue in new_script.get("cues", []):
        name = cue.get("name") or ""
        reading = readings.get(name)
        if not reading:
            missing.append(name)
            continue
        original = display.get(name) or strip_ruby(cue.get("line", ""))
        new_display[name] = original
        if cue.get("line") != reading:
            cue["line"] = reading
            changed += 1
    new_video["display"] = dict(sorted(new_display.items()))

    with open(stage / "script.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(new_script, f, allow_unicode=True, sort_keys=False)
    with open(stage / "video.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(new_video, f, allow_unicode=True, sort_keys=False)
    for name in ("chapters.yaml", "voice_fx.yaml", "sfx.yaml", "bed_mute.yaml"):
        src = project / name
        if src.exists():
            shutil.copy2(src, stage / name)

    assets = Path(args.assets).resolve() if args.assets else project / "assets"
    pruned = 0
    if args.prune_voice:
        for cue in new_script.get("cues", []):
            name = cue.get("name") or ""
            reading = readings.get(name)
            params_path = assets / "voice" / f"{name}.params.yaml"
            wav_path = assets / "voice" / f"{name}.wav"
            if not reading or not params_path.exists():
                continue
            params = load_yaml(params_path)
            old_reading = params.get("reading") or params.get("dialogue") or ""
            if old_reading == reading:
                continue
            for p in (wav_path, params_path):
                if p.exists():
                    p.unlink()
                    pruned += 1
            print(f"  消した: {name}（読みが変わった）")

    print(f"舞台: {stage}")
    print(f"  差し替えた line: {changed} cue / 字幕に元表記を足した: {len(new_display)} cue")
    if missing:
        print(f"  読みの無い cue: {len(missing)}（{ ' '.join(missing[:10]) }{' …' if len(missing) > 10 else ''}）")
    if args.prune_voice:
        print(f"  声を捨てたファイル: {pruned}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="読みの下書き・監査・舞台づくり。")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("draft", help="表示文から reading.yaml の下書きを作る")
    p.add_argument("--project", required=True)
    p.add_argument("--out", default="")
    p.add_argument("--force", action="store_true")

    p = sub.add_parser("audit", help="読みの欠落・残存・字幕の長さを見る")
    p.add_argument("--project", required=True)
    p.add_argument("--phonemize", action="store_true", help="Tsukasa の音素を出す")
    p.add_argument("--cue", default="", help="--phonemize を 1 cue に絞る")
    p.add_argument("--strict", action="store_true", help="警告があれば非 0 で終わる")

    p = sub.add_parser("stage", help="build/<作品>/ に読み差し替えの舞台を作る")
    p.add_argument("--project", required=True)
    p.add_argument("--stage", default="", help="既定は build/<作品名>")
    p.add_argument("--assets", default="", help="声の置き場（既定は <作品>/assets）")
    p.add_argument("--prune-voice", action="store_true", help="読みが変わった cue の声を消す")

    args = ap.parse_args()
    if args.cmd == "draft":
        return draft(args)
    if args.cmd == "audit":
        return audit(args)
    return stage(args)


if __name__ == "__main__":
    sys.exit(main())
