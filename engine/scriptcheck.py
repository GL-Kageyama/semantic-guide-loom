#!/usr/bin/env python3
"""台本・映像設定・読みの参照を、機械的に確かめる。

意味の判断はしない。切れている参照・重複・欠けだけを見る。
guide-script が Markdown から YAML へ起こした直後と、焼く前の点検に使う。

  <venv> engine/scriptcheck.py --project projects/<作品>
  <venv> engine/scriptcheck.py --project projects/<作品> --strict
  <venv> engine/scriptcheck.py --project projects/<作品> --json

終了コード: エラーがあれば 1。警告は既定では 0（--strict なら 1）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

import characters as C
import sal_enums

REPO = Path(__file__).resolve().parent.parent
RUBY = re.compile(r"([^\s《》]+)《([^》]+)》")
MAX_SUBTITLE = 27
# 声を持たない行（「……」だけなど）は build_voice.py が落ちる。間は pause_before に置く。
SPEAKABLE = re.compile(r"[ぁ-んァ-ヶ一-鿿a-zA-Z0-9]")
# 読点を一語ずつ打つ書き方（「鏡の、前に、置く、小さな、装置だ。」）を見る。
# 読点の数と、区切りの平均の長さの両方で判定する。片方だけでは、
# 長い文に正しく打った読点まで拾ってしまう。
MIN_COMMA_FLAG = 3
MAX_MEAN_SEGMENT = 4
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SOURCE_KINDS = {"official", "paper", "reference", "news", "in-work"}
CONFIDENCE = {"high", "medium", "low"}


def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def strip_ruby(text: str) -> str:
    return RUBY.sub(r"\1", text or "")


def cast_ids(name: str) -> set[str] | None:
    path = REPO / "characters" / f"{name}.cast.yaml"
    if not path.exists():
        return None
    cast = load_yaml(path)
    return {c.get("id") for c in cast.get("characters", []) if c.get("id")}


# cue の演技の欄 → SAL の語彙。
VOICE_ENUMS = {
    "emotion": "emotion",
    "speed": "speed",
    "volume": "volume",
    "delivery": "delivery",
    "intensity": "intensity",
}


def check_acting(cue: dict, ids: set[str], faces: dict[str, set[str]],
                 sheets: dict[str, dict | None], enums: dict[str, set[str]],
                 errors: list[str], warnings: list[str]) -> None:
    """演技の欄の参照切れを見る。網羅率などの計測は acting.py の役目。"""
    name = cue.get("name") or "?"
    cid = cue.get("character") or ""

    face = cue.get("face")
    if face:
        if not isinstance(face, str):
            errors.append(f"{name}: face が文字列でない")
        else:
            if str(face).startswith("blink_"):
                errors.append(f"{name}: face {face!r} はまばたき（使わない）")
            if cid and cid in faces and face not in faces[cid]:
                errors.append(f"{name}: face {face!r} が {cid} の expressions に無い")

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

    react = cue.get("react")
    if react is None:
        return
    if not isinstance(react, dict):
        errors.append(f"{name}: react が辞書でない")
        return
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
            else:
                if rface.startswith("blink_"):
                    errors.append(f"{name}: react.{rid}.face {rface!r} はまばたき（使わない）")
                if rid in faces and rface not in faces[rid]:
                    errors.append(f"{name}: react.{rid}.face {rface!r} が "
                                  f"{rid} の expressions に無い")
        if rbeat:
            sheet = sheets.get(rid)
            if sheet is not None and rbeat not in (sheet.get("emotions") or {}):
                errors.append(f"{name}: react.{rid}.beat {rbeat!r} が "
                              f"{rid} の emotions に無い")
            elif sheet is not None and not rface:
                # beat から顔が決まること（決まらないなら face を明示する）
                mapped = ((sheet.get("emotions") or {}).get(rbeat) or {}).get("face")
                if not mapped:
                    errors.append(f"{name}: react.{rid}.beat {rbeat!r} に face が無い"
                                  f"（人物票の emotions に face を書くか、face を明示する）")
                elif rid in faces and mapped not in faces[rid]:
                    errors.append(f"{name}: react.{rid}.beat {rbeat!r} の face "
                                  f"{mapped!r} が {rid} の expressions に無い")
        if mark:
            if not isinstance(mark, str):
                errors.append(f"{name}: react.{rid}.mark が文字列でない")
            elif len(mark) > 3:
                errors.append(f"{name}: react.{rid}.mark が {len(mark)} 字（3 字まで）")


def check_punctuation(name: str, line: str, warnings: list[str]) -> None:
    """読点を一語ずつ打っていないかを見る（日本語の行だけ）。

    「鏡の、前に、置く、小さな、装置だ。」のような行は、声が息継ぎを繰り返し、
    視聴者が文の構造を追えなくなる。読点の数と、区切りの平均の長さの
    両方が小さいときだけ警告する（長い文の正しい読点を拾わないため）。
    """
    if not re.search(r"[ぁ-んァ-ヶ一-鿿]", line):
        return
    commas = line.count("、")
    segments = [s for s in line.split("、") if s]
    if commas >= MIN_COMMA_FLAG and segments:
        mean = sum(len(s) for s in segments) / len(segments)
        if mean <= MAX_MEAN_SEGMENT:
            warnings.append(
                f"{name}: 読点が多すぎる（区切りの平均 {mean:.1f} 字）。"
                f"一語ずつ区切らず、文節の切れ目に打つ: {line!r}"
            )


def check_details(project: Path, video: dict, script: dict,
                  errors: list[str], warnings: list[str]) -> None:
    """details の形・所属・順序・容量を見る。

    時刻の検査はしない（古い mix.yaml を見る可能性がある）。実尺での判定は
    export_timeline が章の start を確定した後に行う。
    """
    chapters = video.get("chapters") or {}
    if not isinstance(chapters, dict):
        return
    if not any(isinstance(ch, dict) and ch.get("details") for ch in chapters.values()):
        return

    cue_names = [c.get("name") for c in (script.get("cues") or []) if c.get("name")]
    pos = {name: i for i, name in enumerate(cue_names)}
    chapter_rows = []
    for cue_name, ch in chapters.items():
        if not isinstance(ch, dict) or cue_name not in pos:
            continue
        chapter_rows.append((pos[cue_name], cue_name, ch))
    chapter_rows.sort()

    font_checks: list[tuple[str, dict, dict]] = []
    for k, (idx, cue_name, ch) in enumerate(chapter_rows):
        end_idx = chapter_rows[k + 1][0] if k + 1 < len(chapter_rows) else len(cue_names)
        details = ch.get("details")
        if details is None:
            continue
        if not isinstance(details, list):
            errors.append(f"{cue_name}: details が配列でない")
            continue
        seen: set[str] = set()
        prev_idx = idx
        for j, detail in enumerate(details, 1):
            label = f"{cue_name} details[{j}]"
            if not isinstance(detail, dict):
                errors.append(f"{label}: 辞書でない")
                continue
            unknown = sorted(set(detail) - {"cue", "head", "lines", "fact"})
            if unknown:
                warnings.append(f"{label}: 知らない欄 {unknown}（型が将来読む欄は弾かない）")

            dcue = detail.get("cue")
            if not isinstance(dcue, str) or not dcue:
                errors.append(f"{label}: cue が空")
                continue
            di = pos.get(dcue)
            if di is None:
                errors.append(f"{label}: script.yaml に無い cue {dcue!r}")
                continue
            if not (idx <= di < end_idx):
                errors.append(f"{label}: cue {dcue!r} が章の範囲外")
                continue
            if dcue in seen:
                errors.append(f"{label}: cue {dcue!r} が重複")
            seen.add(dcue)
            if di <= prev_idx:
                errors.append(f"{label}: 台本順で増えない cue {dcue!r}")
            prev_idx = di
            if di == idx:
                warnings.append(f"{label}: 最初の詳細が章の頭 cue と同じ（key を読む間が無い）")

            head = detail.get("head")
            if not isinstance(head, str) or not head:
                errors.append(f"{label}: head が空")
            elif "\n" in head:
                errors.append(f"{label}: head に改行がある（1 行にする）")

            lines = detail.get("lines")
            if not isinstance(lines, list) or not lines:
                errors.append(f"{label}: lines が空")
            else:
                if len(lines) > 4:
                    errors.append(f"{label}: lines が {len(lines)} 項目（4 項目まで）")
                for n, line in enumerate(lines, 1):
                    if not isinstance(line, str) or not line:
                        errors.append(f"{label}: lines[{n}] が空")
                    elif "\n" in line:
                        errors.append(f"{label}: lines[{n}] に改行がある（1 表示行に割る）")
            if isinstance(head, str) and head and isinstance(lines, list) and lines:
                font_checks.append((label, detail, ch))

    template = video.get("template") or ""
    tpl_path = REPO / "references" / "templates" / template / "template.yaml"
    if not template or not tpl_path.exists():
        warnings.append("details があるが型を読めない（head 幅と容量の検査を飛ばした）")
        return
    tpl = load_yaml(tpl_path)
    if (tpl.get("layout") != "dialogue_bust"
            or not (tpl.get("panel") or {}).get("detail")):
        warnings.append(
            "details があるが、この型は詳細カードを描かない"
            "（layout が dialogue_bust でないか、panel.detail が無い）"
        )
        return
    try:
        import common as K
        from layouts.dialogue_bust import detail_geometry
    except Exception as exc:  # Pillow / 書体 / レイアウトが無い環境
        warnings.append(f"書体かレイアウトを読めないので、head 幅と容量の検査を飛ばした（{exc}）")
        return
    K.TPL = tpl
    K.PAL = tpl.get("palette") or {}
    canvas_h = float((tpl.get("canvas") or {}).get("height", 720))
    K.SCALE = float(video.get("height", 720)) / canvas_h
    geo_by_ch: dict[str, dict] = {}
    try:
        for label, detail, ch in font_checks:
            key_name = str(id(ch))
            if key_name not in geo_by_ch:
                geo_by_ch[key_name] = detail_geometry({
                    "label": ch.get("label", ""),
                    "title": ch.get("title", ""),
                    "term": ch.get("term", ""),
                    "key": ch.get("key", ""),
                })
            geo = geo_by_ch[key_name]
            head = detail["head"]
            if geo["head_font"].getlength(head) > geo["inner_width"]:
                errors.append(f"{label}: head が 1 行に収まらない（{head!r}）")
            n = len(detail["lines"])
            if n > geo["capacity"]:
                errors.append(f"{label}: {n} 行（容量 {geo['capacity']} 行）")
            for line in detail["lines"]:
                if geo["line_font"].getlength(line) > geo["inner_width"]:
                    warnings.append(
                        f"{label}: 行が自動折り返しになる（1 表示行に割り直す）: {line!r}"
                    )
    except (KeyError, TypeError, ValueError, OSError) as exc:
        warnings.append(f"型の panel.detail を読めないので、head 幅と容量の検査を飛ばした（{exc}）")


def check_research(project: Path, video: dict,
                   errors: list[str], warnings: list[str]) -> None:
    """research/ の出典と事実、details[].fact の参照を見る。

    形の検査は schemas/research.schema.json と tools/check_layout.py が持つ。
    ここは参照切れと、カードに使ってよい確度かを見る。
    """
    chapters = video.get("chapters") or {}
    details: list[tuple[str, int, dict]] = []
    if isinstance(chapters, dict):
        for ch_name, ch in chapters.items():
            if not isinstance(ch, dict):
                continue
            for i, detail in enumerate(ch.get("details") or [], 1):
                if isinstance(detail, dict):
                    details.append((ch_name, i, detail))

    research = project / "research"
    sources_path = research / "sources.yaml"
    facts_path = research / "facts.yaml"
    if not research.exists():
        if details:
            warnings.append(
                "details があるが research/ が無い（事実の出典を辿れない。--strict で失敗）"
            )
        return

    sources: list = []
    if not sources_path.exists():
        errors.append("research/sources.yaml が無い")
    else:
        doc = load_yaml(sources_path)
        value = doc.get("sources") if isinstance(doc, dict) else None
        if not isinstance(value, list):
            errors.append("research/sources.yaml: sources が配列でない")
        else:
            sources = value

    source_ids: set[str] = set()
    for i, source in enumerate(sources, 1):
        if not isinstance(source, dict):
            errors.append(f"research/sources.yaml: sources[{i}] が辞書でない")
            continue
        sid = source.get("id")
        if not isinstance(sid, str) or not ID_RE.match(sid):
            errors.append(f"research/sources.yaml: sources[{i}].id が不正（{sid!r}）")
        elif sid in source_ids:
            errors.append(f"research/sources.yaml: id が重複（{sid}）")
        else:
            source_ids.add(sid)
        label = sid if isinstance(sid, str) else f"sources[{i}]"
        if not source.get("title"):
            errors.append(f"research/sources.yaml: {label} に title が無い")
        kind = source.get("kind")
        if kind not in SOURCE_KINDS:
            errors.append(f"research/sources.yaml: {label} の kind が不正（{kind!r}）")
        accessed = source.get("accessed")
        if not isinstance(accessed, str) or not DATE_RE.match(accessed):
            errors.append(
                f"research/sources.yaml: {label} の accessed が YYYY-MM-DD でない"
                f"（引用符で囲む: {accessed!r}）"
            )
        if source.get("confidence") is not None and source.get("confidence") not in CONFIDENCE:
            errors.append(f"research/sources.yaml: {label} の confidence が不正")
        url = source.get("url")
        path = source.get("path")
        if not url and not path:
            errors.append(f"research/sources.yaml: {label} に url も path も無い")
        if url and not str(url).startswith(("http://", "https://")):
            errors.append(f"research/sources.yaml: {label} の url が http(s) でない")

    facts: list = []
    fact_map: dict[str, dict] = {}
    if not facts_path.exists():
        if details:
            errors.append("research/facts.yaml が無い（details[].fact を解決できない）")
    else:
        doc = load_yaml(facts_path)
        value = doc.get("facts") if isinstance(doc, dict) else None
        if not isinstance(value, list):
            errors.append("research/facts.yaml: facts が配列でない")
        else:
            facts = value

    for i, fact in enumerate(facts, 1):
        if not isinstance(fact, dict):
            errors.append(f"research/facts.yaml: facts[{i}] が辞書でない")
            continue
        fid = fact.get("id")
        if not isinstance(fid, str) or not ID_RE.match(fid):
            errors.append(f"research/facts.yaml: facts[{i}].id が不正（{fid!r}）")
        elif fid in fact_map:
            errors.append(f"research/facts.yaml: id が重複（{fid}）")
        else:
            fact_map[fid] = fact
        label = fid if isinstance(fid, str) else f"facts[{i}]"
        statement = fact.get("statement")
        if not isinstance(statement, str) or not statement.strip():
            errors.append(f"research/facts.yaml: {label} に statement が無い")
        fsources = fact.get("sources")
        if not isinstance(fsources, list) or not fsources:
            errors.append(f"research/facts.yaml: {label} に sources が無い")
        else:
            for sid in fsources:
                if sid not in source_ids:
                    errors.append(
                        f"research/facts.yaml: {label} の source {sid!r} が "
                        "sources.yaml に無い"
                    )
        if fact.get("confidence") not in CONFIDENCE:
            errors.append(f"research/facts.yaml: {label} の confidence が不正")

    for ch_name, i, detail in details:
        fid = detail.get("fact")
        if not fid:
            warnings.append(
                f"video.yaml {ch_name} details[{i}]: fact が無い"
                "（新しい作品は research/facts.yaml の id を付ける）"
            )
            continue
        if not isinstance(fid, str) or fid not in fact_map:
            errors.append(
                f"video.yaml {ch_name} details[{i}]: fact {fid!r} が "
                "research/facts.yaml に無い"
            )
            continue
        if fact_map[fid].get("confidence") == "low":
            warnings.append(
                f"video.yaml {ch_name} details[{i}]: fact {fid!r} は confidence: low"
            )


def check(args) -> int:
    project = Path(args.project)
    errors: list[str] = []
    warnings: list[str] = []

    script_path = project / "script.yaml"
    if not script_path.exists():
        errors.append(f"script.yaml が無い: {script_path}")
        return report(errors, warnings, args)
    script = load_yaml(script_path)
    video = load_yaml(project / "video.yaml") if (project / "video.yaml").exists() else {}
    display = video.get("display") or {}
    cues = script.get("cues") or []
    if not cues:
        errors.append("script.yaml に cues が無い")

    names: list[str] = []
    for i, cue in enumerate(cues, 1):
        name = cue.get("name") or ""
        if not name:
            errors.append(f"cues[{i}]: name が無い")
            continue
        names.append(name)
        line = (cue.get("line") or "").strip()
        if not line:
            errors.append(f"{name}: line が空")
        elif not SPEAKABLE.search(strip_ruby(line)):
            errors.append(
                f"{name}: 声を持たない行（{line!r}）。間は次の cue の pause_before に置く"
            )
        else:
            check_punctuation(name, strip_ruby(line), warnings)
    dupes = sorted({n for n in names if names.count(n) > 1})
    for name in dupes:
        errors.append(f"cue 名が重複している: {name}")
    name_set = set(names)

    if video.get("cast"):
        cast_name = video["cast"]
        ids = cast_ids(cast_name)
        if ids is None:
            errors.append(f"cast が無い: characters/{cast_name}.cast.yaml")
        else:
            cast_doc = load_yaml(REPO / "characters" / f"{cast_name}.cast.yaml")
            faces = {c.get("id"): set(c.get("expressions") or [])
                     for c in cast_doc.get("characters", []) if c.get("id")}
            sheets = {cid: C.sheet_for_cast(cast_name, cid) for cid in ids}
            enums = sal_enums.load()
            if not enums and any(cue.get(k) for cue in cues for k in VOICE_ENUMS):
                warnings.append("SAL の語彙が読めない（SAL= で場所を指定）。"
                                "声の語彙の検査は飛ばした")
            for cue in cues:
                cid = cue.get("character") or ""
                if cid and cid not in ids:
                    errors.append(f"{cue.get('name')}: character {cid!r} が cast に無い")
                check_acting(cue, ids, faces, sheets, enums, errors, warnings)

    template = video.get("template") or ""
    if template and not (REPO / "references" / "templates" / template / "template.yaml").exists():
        errors.append(f"型が無い: references/templates/{template}/template.yaml")

    for name in sorted(set(display) - name_set):
        errors.append(f"video.yaml display: script.yaml に無い cue {name}")
    for name in sorted((video.get("chapters") or {}).keys() - name_set):
        errors.append(f"video.yaml chapters: script.yaml に無い cue {name}")

    chime_path = project / "chapters.yaml"
    if chime_path.exists():
        chimes = load_yaml(chime_path)
        if isinstance(chimes, list):
            for name in chimes:
                if name not in name_set:
                    errors.append(f"chapters.yaml: script.yaml に無い cue {name}")
            video_ch = set((video.get("chapters") or {}).keys())
            if video_ch and set(chimes) != video_ch:
                warnings.append(
                    f"chapters.yaml と video.yaml の章が違う（チャイム {len(chimes)} / 札 {len(video_ch)}）"
                )
        else:
            errors.append("chapters.yaml は cue 名の配列であること")
        if isinstance(chimes, list) and chimes and not (project / "assets" / "sfx" / "chime.wav").exists():
            warnings.append(
                "chapters.yaml があるが assets/sfx/chime.wav が無い（章の印が鳴らない）"
            )

    reading_path = project / "reading.yaml"
    if reading_path.exists():
        readings = (load_yaml(reading_path).get("readings") or {})
        for name in names:
            if not readings.get(name):
                warnings.append(f"{name}: reading.yaml に読みが無い")
        for name in sorted(set(readings) - name_set):
            errors.append(f"reading.yaml: script.yaml に無い cue {name}")

    for cue in cues:
        name = cue.get("name") or "?"
        text = strip_ruby(display.get(name) or cue.get("line", ""))
        if len(text) > MAX_SUBTITLE:
            warnings.append(f"{name}: 字幕が {len(text)} 字（{MAX_SUBTITLE} 字超）")

    check_details(project, video, script, errors, warnings)
    check_research(project, video, errors, warnings)

    return report(errors, warnings, args, counts=(len(names), len(video.get("chapters") or {})))


def report(errors: list[str], warnings: list[str], args, counts: tuple[int, int] | None = None) -> int:
    if args.json:
        print(json.dumps({"ok": not errors, "errors": errors, "warnings": warnings},
                         ensure_ascii=False, indent=2))
    else:
        if counts:
            print(f"{counts[0]} cue / {counts[1]} 章")
        if errors:
            print(f"エラー {len(errors)} 件")
            for line in errors:
                print(f"  {line}")
        if warnings:
            print(f"警告 {len(warnings)} 件")
            for line in warnings:
                print(f"  {line}")
        if not errors and not warnings:
            print("ok")
        elif not errors:
            print("エラーなし")
    if errors:
        return 1
    if warnings and args.strict:
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="台本・映像設定・読みの参照を確かめる。")
    ap.add_argument("--project", required=True)
    ap.add_argument("--strict", action="store_true", help="警告も失敗として扱う")
    ap.add_argument("--json", action="store_true")
    return check(ap.parse_args())


if __name__ == "__main__":
    sys.exit(main())
