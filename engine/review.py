#!/usr/bin/env python3
"""評議会の JSON を集計し、版ごとの平均を記録する。

評価そのものはスキル（guide-script）が評議会に掛けて行う。この道具は、
`review/reports/<版>/*.json` に残った `primary_score` を読み、平均と次元を
`review/scores.yaml` に書き、推移表を出す。判定はしない。採用は人が決める。

  <venv> engine/review.py table  --project projects/black-swan-ai
  <venv> engine/review.py record --project projects/black-swan-ai
  <venv> engine/review.py record --project projects/black-swan-ai --adopted v7
  <venv> engine/review.py validate --project projects/black-swan-ai

合格ラインは既定 60。`table` は採用済みの版と、合格圏で最も高い版に印を付ける。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
DEFAULT_THRESHOLD = 60.0


def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def natural_key(text: str) -> list:
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", text)]


def round2(value: float) -> float:
    """README の丸め（四捨五入）に合わせる。Python の round は 60.625 を 60.62 にする。"""
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def find_reports(project: Path) -> dict[str, dict]:
    root = project / "review" / "reports"
    out: dict[str, dict] = {}
    if not root.is_dir():
        return out
    for d in sorted((p for p in root.iterdir() if p.is_dir()), key=lambda p: natural_key(p.name)):
        scores: dict[str, float] = {}
        errors: list[str] = []
        for p in sorted(d.glob("*.json")):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"{p.name}: {exc}")
                continue
            score = data.get("primary_score")
            if isinstance(score, (int, float)) and not isinstance(score, bool):
                scores[p.stem] = float(score)
            else:
                errors.append(f"{p.name}: primary_score が無い")
        out[d.name] = {"count": len(scores), "scores": scores, "errors": errors}
    return out


def mean_of(scores: dict[str, float]) -> float | None:
    if not scores:
        return None
    return round2(sum(scores.values()) / len(scores))


def existing_index(project: Path) -> dict:
    path = project / "review" / "scores.yaml"
    if not path.exists():
        return {}
    return load_yaml(path)


def table(args) -> int:
    project = Path(args.project)
    reports = find_reports(project)
    if not reports:
        print(f"評価が無い: {project / 'review' / 'reports'}")
        return 1

    index = existing_index(project)
    adopted = index.get("adopted") or ""
    means = {name: mean_of(r["scores"]) for name, r in reports.items()}
    eligible = {name: m for name, m in means.items() if m is not None and m >= args.threshold}
    best = max(eligible, key=lambda k: eligible[k]) if eligible else ""

    print("| 版 | 平均 | 次元 | 採否 |")
    print("| --- | ---: | ---: | --- |")
    for name in reports:
        m = means[name]
        mark = ""
        if name == adopted:
            mark = "採用"
        elif name == best and name != adopted:
            mark = "合格圏の最高"
        if m is None:
            print(f"| {name} | — | 0 | {mark or '評価なし'} |")
        else:
            print(f"| {name} | {m:.2f} | {reports[name]['count']} | {mark} |")
    if not adopted and best:
        print(f"\n合格ライン {args.threshold:g} を超えた最高は {best}（{means[best]:.2f}）。採用はまだ記録されていない。")
    for name, r in reports.items():
        if r["errors"]:
            print(f"\n{name}: {len(r['errors'])} 件の不備")
            for err in r["errors"]:
                print(f"  {err}")
    return 0


def record(args) -> int:
    project = Path(args.project)
    reports = find_reports(project)
    if not reports:
        print(f"評価が無い: {project / 'review' / 'reports'}")
        return 1

    index = existing_index(project)
    adopted = args.adopted or index.get("adopted") or ""
    if adopted and adopted not in reports:
        print(f"--adopted {adopted} の評価が無い")
        return 1

    versions: dict[str, dict] = {}
    for name, r in reports.items():
        mean = mean_of(r["scores"])
        entry: dict = {
            "mean": mean,
            "count": r["count"],
            "scores": {k: int(v) if float(v).is_integer() else v for k, v in r["scores"].items()},
        }
        if r["errors"]:
            entry["errors"] = r["errors"]
        versions[name] = entry

    out: dict = {"threshold": args.threshold}
    if adopted:
        out["adopted"] = adopted
    out["versions"] = versions

    path = project / "review" / "scores.yaml"
    with open(path, "w", encoding="utf-8") as f:
        f.write("# 評議会の採点。engine/review.py record が reports/ から作る。\n")
        f.write("# 平均は 8 次元の primary_score。採用は人が決め、adopted に残す。\n")
        yaml.safe_dump(out, f, allow_unicode=True, sort_keys=False)
    print(f"書いた: {path}")

    for name, entry in versions.items():
        m = entry["mean"]
        print(f"  {name}: {m:.2f}（{entry['count']} 次元）" if m is not None else f"  {name}: 評価なし")
    return 0


def council_root() -> Path | None:
    for candidate in (Path.home() / "AI創作工房" / "novel-council-layer", REPO.parent / "novel-council-layer"):
        if (candidate / "utils" / "validate_output.py").exists():
            return candidate
    return None


def validate(args) -> int:
    project = Path(args.project)
    root = council_root()
    if root is None:
        print("novel-council-layer が見つからない（COUNCIL は未対応。並びに置く）")
        return 1
    reports = project / "review" / "reports"
    if not reports.is_dir():
        print(f"評価が無い: {reports}")
        return 1
    versions = [args.version] if args.version else [
        d.name for d in sorted((p for p in reports.iterdir() if p.is_dir()), key=lambda p: natural_key(p.name))
    ]
    checks = root / "utils" / "validate_output.py"
    bad = 0
    for version in versions:
        for p in sorted((reports / version).glob("*.json")):
            proc = subprocess.run(
                [sys.executable, str(checks), "--json", str(p)],
                capture_output=True, text=True,
            )
            ok = proc.returncode == 0
            if not ok:
                bad += 1
            print(f"{version}/{p.name}: {'ok' if ok else 'NG'}")
            if not ok:
                print((proc.stdout or proc.stderr).strip())
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="評議会の採点を集計し、推移を記録する。")
    sub = ap.add_subparsers(dest="cmd", required=True)

    for cmd, help_text in (("table", "版ごとの平均と採否を出す"),
                           ("record", "review/scores.yaml を書く")):
        p = sub.add_parser(cmd, help=help_text)
        p.add_argument("--project", required=True)
        p.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
        if cmd == "record":
            p.add_argument("--adopted", default="", help="採用した版（省略時は既存の値を保つ）")

    p = sub.add_parser("validate", help="評価者 JSON を novel-council-layer で検証する")
    p.add_argument("--project", required=True)
    p.add_argument("--version", default="", help="版を絞る（省略時は全部）")

    args = ap.parse_args()
    if args.cmd == "table":
        return table(args)
    if args.cmd == "record":
        return record(args)
    return validate(args)


if __name__ == "__main__":
    sys.exit(main())
