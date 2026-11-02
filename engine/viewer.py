#!/usr/bin/env python3
"""解説の門 — 初見の視聴者テストと、説明の評価を集計する。

文学の評議会（engine/review.py）とは別の物差し。**平均に混ぜない。**
台本だけを渡した初見の読者が、出来事・原因・数字の分母を復元できるかを見る。

入力（版ごとのディレクトリ）:

  review/viewers/<版>/
    facts.yaml        視聴者が答えられるべき事実（id / question / answer）
    r1.json r2.json … 初見の読者の返答（reader_id / clarity / recovered / unclear）
    explanation.json  説明の設計の評価（primary_score / critical / missing）

出力:

  review/viewers/<版>.yaml   集計と門の判定（この道具が書く）

  <venv> engine/viewer.py baseline --project projects/<作品> --version baseline-plain
  <venv> engine/viewer.py record   --project projects/<作品> --version v7
  <venv> engine/viewer.py table    --project projects/<作品>
  <venv> engine/viewer.py compare  --project projects/<作品> --before v6 --after v7

門（--strict で失敗扱い）:
  - 初見の理解度の平均 >= 75（平文の基準を使わないとき）
  - --baseline <基準> を渡したときは、しきい値は「基準の平均 − --gap（既定 10）」
  - すべての事実が、読者の 2/3 以上に復元されている（yes=1, partial=0.5, no=0）
  - 説明の評価 >= 75、かつ critical が無い

平文の基準（baseline）は、同じ事実を人物も感情の層も無しで書いた台本を、
同じ 3 人に読ませたもの。掛け合いの台本の理解度は、この基準からの差で見る。
絶対値 75 は、平文で書いた解説のための数字で、題材そのものが難しい場合は
平文でも届かない。基準を測ることで「題材が難しい」と「調子が意味を落とした」を
分けて見る。
"""
from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
DEFAULT_CLARITY = 75.0
DEFAULT_FACT = 2 / 3
DEFAULT_EXPLANATION = 75.0
DEFAULT_GAP = 10.0
RECOVERY = {"yes": 1.0, "partial": 0.5, "no": 0.0}


def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def round2(value: float) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def viewers_root(project: Path) -> Path:
    return project / "review" / "viewers"


def version_dir(project: Path, version: str) -> Path:
    return viewers_root(project) / version


def load_facts(project: Path, version: str, facts_path: str = "") -> list[dict]:
    path = Path(facts_path) if facts_path else version_dir(project, version) / "facts.yaml"
    if not path.exists():
        return []
    doc = load_yaml(path)
    facts = doc.get("facts") if isinstance(doc, dict) else doc
    out = []
    for fact in facts or []:
        if isinstance(fact, dict) and fact.get("id"):
            out.append(fact)
    return out


def load_readers(project: Path, version: str) -> dict[str, dict]:
    root = version_dir(project, version)
    out: dict[str, dict] = {}
    if not root.is_dir():
        return out
    for path in sorted(root.glob("*.json")):
        if path.name == "explanation.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            out[path.stem] = {"error": str(exc)}
            continue
        rid = data.get("reader_id") or path.stem
        out[rid] = data
    return out


def load_explanation(project: Path, version: str) -> dict | None:
    path = version_dir(project, version) / "explanation.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def summarize(project: Path, version: str, args, baseline: dict | None = None) -> dict:
    facts = load_facts(project, version, args.facts)
    readers = load_readers(project, version)
    explanation = load_explanation(project, version)

    clarity: dict[str, float] = {}
    for rid, data in readers.items():
        value = data.get("clarity")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            clarity[rid] = float(value)
    mean_clarity = round2(sum(clarity.values()) / len(clarity)) if clarity else None
    threshold = args.clarity
    if baseline is not None:
        threshold = baseline["mean"] - args.gap
    clarity_pass = mean_clarity is not None and mean_clarity >= threshold

    clarity_block = {"mean": mean_clarity, "readers": clarity}
    if baseline is not None:
        clarity_block["baseline"] = {
            "version": baseline["version"],
            "mean": baseline["mean"],
            "gap": round2(args.gap),
        }
    clarity_block["threshold"] = round2(threshold)
    clarity_block["pass"] = clarity_pass

    fact_rows: dict[str, dict] = {}
    for fact in facts:
        fid = fact["id"]
        counts = {k: 0 for k in RECOVERY}
        for data in readers.values():
            level = str((data.get("recovered") or {}).get(fid, "no") or "no")
            counts[level if level in counts else "no"] += 1
        total = sum(counts.values())
        score = (sum(RECOVERY[k] * n for k, n in counts.items()) / total) if total else 0.0
        fact_rows[fid] = {
            **counts,
            "score": round2(score),
            "pass": bool(total and score >= args.fact),
        }
    facts_pass = bool(facts) and bool(fact_rows) and all(r["pass"] for r in fact_rows.values())

    exp_score = None
    exp_critical = False
    if explanation:
        value = explanation.get("primary_score")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            exp_score = float(value)
        exp_critical = bool(explanation.get("critical"))
    explanation_pass = (
        exp_score is not None and exp_score >= args.explanation and not exp_critical
    )

    return {
        "version": version,
        "clarity": clarity_block,
        "facts": {
            "items": fact_rows,
            "threshold": round2(args.fact),
            "pass": facts_pass,
        },
        "explanation": {
            "score": exp_score,
            "critical": exp_critical,
            "threshold": args.explanation,
            "pass": explanation_pass,
        },
        "pass": clarity_pass and facts_pass and explanation_pass,
    }


def load_baseline(project: Path, name: str) -> dict | None:
    """平文の基準の集計を読む。基準は engine/viewer.py baseline が作る。"""
    path = viewers_root(project) / f"{name}.yaml"
    if not path.exists():
        print(f"基準が無い: {path}", file=sys.stderr)
        return None
    data = load_yaml(path)
    if data.get("kind") != "baseline":
        print(f"平文の基準ではない: {path}（engine/viewer.py baseline で作る）",
              file=sys.stderr)
        return None
    mean = (data.get("clarity") or {}).get("mean")
    if not isinstance(mean, (int, float)) or isinstance(mean, bool):
        print(f"基準の理解度が無い: {path}", file=sys.stderr)
        return None
    return {"version": name, "mean": float(mean)}


def baseline(args) -> int:
    """平文の基準を集計する。事実と説明の判定はしない（理解度だけ）。"""
    project = Path(args.project)
    version = args.version
    readers = load_readers(project, version)
    clarity: dict[str, float] = {}
    for rid, data in readers.items():
        value = data.get("clarity")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            clarity[rid] = float(value)
    if not clarity:
        print(f"読者の返答が無い: {version_dir(project, version)}", file=sys.stderr)
        return 1
    mean = round2(sum(clarity.values()) / len(clarity))
    summary = {
        "kind": "baseline",
        "version": version,
        "clarity": {"mean": mean, "readers": clarity},
    }
    path = viewers_root(project) / f"{version}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("# 平文の基準。同じ事実を人物も感情の層も無しで書いた台本の理解度。\n")
        f.write("# engine/viewer.py baseline が作る。門の判定には使わない（record の --baseline）。\n")
        yaml.safe_dump(summary, f, allow_unicode=True, sort_keys=False)
    print(f"{version}: 平文の基準の初見の理解度 {mean:.2f}")
    print(f"\n書いた: {path}")
    return 0


def record(args) -> int:
    project = Path(args.project)
    version = args.version
    reference = None
    if args.baseline:
        reference = load_baseline(project, args.baseline)
        if reference is None:
            return 1
        if reference["mean"] < 60:
            print(f"注意: 平文の基準が {reference['mean']:.2f}。平文でも伝わっていない。"
                  f"台本ではなく設計（事実の選び方・順序）を見直す。", file=sys.stderr)
    summary = summarize(project, version, args, reference)
    path = viewers_root(project) / f"{version}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("# 解説の門。engine/viewer.py record が viewers/<版>/ から作る。\n")
        f.write("# 文学の評議会（review/scores.yaml）とは別の物差し。平均に混ぜない。\n")
        yaml.safe_dump(summary, f, allow_unicode=True, sort_keys=False)
    print_summary(summary)
    print(f"\n書いた: {path}")
    return 0 if summary["pass"] or not args.strict else 1


def print_summary(summary: dict) -> None:
    clarity = summary["clarity"]
    mean = clarity["mean"]
    base = clarity.get("baseline")
    origin = ""
    if base:
        origin = f"（平文の基準 {base['version']} {base['mean']:.2f} − {base['gap']:g}）"
    print(f"{summary['version']}: 初見の理解度 "
          f"{'—' if mean is None else f'{mean:.2f}'} / {clarity['threshold']:g}"
          f"{origin} "
          f"({'通過' if clarity['pass'] else '不足'})")
    if summary["facts"]["items"]:
        for fid, row in summary["facts"]["items"].items():
            print(f"  {fid}: yes {row['yes']} / partial {row['partial']} / no {row['no']} "
                  f"— {row['score']:.2f} ({'通過' if row['pass'] else '不足'})")
    else:
        print("  事実: facts.yaml が無い（判定できない）")
    exp = summary["explanation"]
    score = "—" if exp["score"] is None else f"{exp['score']:.0f}"
    print(f"  説明の評価: {score} / {exp['threshold']:g}"
          f"{'（critical あり）' if exp['critical'] else ''}"
          f" ({'通過' if exp['pass'] else '不足'})")
    print(f"  門: {'通過' if summary['pass'] else '未通過'}")


def table(args) -> int:
    root = viewers_root(Path(args.project))
    files = sorted(root.glob("*.yaml"))
    if not files:
        print(f"視聴者テストが無い: {root}")
        return 1
    print("| 版 | 初見の理解度 | 事実 | 説明 | 門 |")
    print("| --- | ---: | --- | ---: | --- |")
    for path in files:
        data = load_yaml(path)
        if data.get("kind") == "baseline":
            continue
        clarity = data.get("clarity") or {}
        facts = data.get("facts") or {}
        exp = data.get("explanation") or {}
        mean = clarity.get("mean")
        fact_ok = "通過" if facts.get("pass") else "不足"
        exp_score = exp.get("score")
        print(f"| {data.get('version', path.stem)} | "
              f"{'—' if mean is None else f'{mean:.2f}'} | {fact_ok} | "
              f"{'—' if exp_score is None else f'{exp_score:.0f}'} | "
              f"{'通過' if data.get('pass') else '未通過'} |")
    return 0


def compare(args) -> int:
    root = viewers_root(Path(args.project))
    a_path, b_path = root / f"{args.before}.yaml", root / f"{args.after}.yaml"
    for path in (a_path, b_path):
        if not path.exists():
            print(f"集計が無い: {path}")
            return 1
    a, b = load_yaml(a_path), load_yaml(b_path)
    am, bm = (a.get("clarity") or {}).get("mean"), (b.get("clarity") or {}).get("mean")
    print("| 指標 | %s | %s | 差 |" % (args.before, args.after))
    print("| --- | ---: | ---: | ---: |")
    if am is not None and bm is not None:
        print(f"| 初見の理解度 | {am:.2f} | {bm:.2f} | {bm - am:+.2f} |")
    ae = (a.get("explanation") or {}).get("score")
    be = (b.get("explanation") or {}).get("score")
    if ae is not None and be is not None:
        print(f"| 説明の評価 | {ae:.0f} | {be:.0f} | {be - ae:+.0f} |")
    af = (a.get("facts") or {}).get("items") or {}
    bf = (b.get("facts") or {}).get("items") or {}
    for fid in sorted(set(af) | set(bf)):
        av = (af.get(fid) or {}).get("score")
        bv = (bf.get(fid) or {}).get("score")
        if av is not None and bv is not None:
            print(f"| 事実: {fid} | {av:.2f} | {bv:.2f} | {bv - av:+.2f} |")
    print(f"| **門** | {'通過' if a.get('pass') else '未通過'} | "
          f"{'通過' if b.get('pass') else '未通過'} | |")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="初見の視聴者テストと説明の評価を集計する。")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("baseline", help="平文の基準を集計して viewers/<基準>.yaml を書く")
    p.add_argument("--project", required=True)
    p.add_argument("--version", required=True)

    p = sub.add_parser("record", help="viewers/<版>/ を集計して viewers/<版>.yaml を書く")
    p.add_argument("--project", required=True)
    p.add_argument("--version", required=True)
    p.add_argument("--facts", default="", help="facts.yaml の場所（既定は viewers/<版>/facts.yaml）")
    p.add_argument("--clarity", type=float, default=DEFAULT_CLARITY)
    p.add_argument("--fact", type=float, default=DEFAULT_FACT)
    p.add_argument("--explanation", type=float, default=DEFAULT_EXPLANATION)
    p.add_argument("--baseline", default="", help="平文の基準の版（viewers/<版>.yaml）")
    p.add_argument("--gap", type=float, default=DEFAULT_GAP,
                   help="平文の基準から許す理解度の差（既定 10）")
    p.add_argument("--strict", action="store_true", help="門を通らなければ失敗にする")

    p = sub.add_parser("table", help="版ごとの門を出す")
    p.add_argument("--project", required=True)

    p = sub.add_parser("compare", help="2 版の差を出す")
    p.add_argument("--project", required=True)
    p.add_argument("--before", required=True)
    p.add_argument("--after", required=True)

    args = ap.parse_args()
    if args.cmd == "baseline":
        return baseline(args)
    if args.cmd == "record":
        return record(args)
    if args.cmd == "table":
        return table(args)
    return compare(args)


if __name__ == "__main__":
    sys.exit(main())
