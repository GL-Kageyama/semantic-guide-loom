#!/usr/bin/env python3
"""話に合わせた敷き音（BGM）を、台本から作る。

意図は作品の `bgm.yaml` が持ち、音は semantic-audio-loom の MusicGen が作る。
この道具は 3 つを担う:

  suggest  台本・章から bgm.yaml の下書きを出す（意味の判断はスキルがする）
  generate 30 秒 × 数本を別シードで作り、クロスフェードして assets/bgm/<name>.wav
  mix      assemble.py が書いた mix.yaml の bed 利得と duck を bgm.yaml の値へ直し、
           もう一度だけ混ぜる（make.sh のたびに −30/14 へ戻るのを防ぐ）

  <venv> engine/bgm.py suggest  --project projects/<作品>
  <venv> engine/bgm.py generate --project projects/<作品> [--dry-run] [--force]
  <venv> engine/bgm.py mix      --project projects/<作品> [--stage build/<作品>]

`generate` は入力（prompt・シード・分割・クロスフェード・利得）が変わらなければ
飛ばす。`--force` で作り直す。`mix` は音を作らない。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
DEFAULT_PROMPT = (
    "A continuous soft ambient pad, warm evolving chords, very subtle felt piano "
    "notes, calm and curious, slight unease, steady background texture, no drums, "
    "no vocals, low dynamic"
)
DEFAULT_MIX = {
    "gain_db": -8.0,
    "duck": {"threshold_db": -30.0, "depth_db": 3.0, "attack_s": 0.03, "release_s": 0.45},
}
STOP = set(
    "こと もの ため ところ そう これ それ あれ ここ そこ どこ 人 中 前 後 今 時 年 月 日 "
    "僕 私 君 さん です ます そう でも じゃあ そして だから しかし".split()
)


def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def sal_root() -> Path:
    sal = Path(os.environ.get("SAL", REPO.parent / "semantic-audio-loom"))
    if not (sal / "semantic_audio_loom").is_dir():
        raise SystemExit(f"semantic-audio-loom が無い: {sal}（SAL で指定）")
    return sal


def project_text(project: Path) -> tuple[list[str], dict]:
    script = load_yaml(project / "script.yaml")
    video = load_yaml(project / "video.yaml") if (project / "video.yaml").exists() else {}
    display = video.get("display") or {}
    lines = [display.get(c.get("name")) or c.get("line", "") for c in script.get("cues", [])]
    return [line for line in lines if line], video


def keywords(lines: list[str], limit: int = 12) -> list[str]:
    try:
        from fugashi import Tagger
    except ImportError:
        return []
    tagger = Tagger()
    counts: dict[str, int] = {}
    for line in lines:
        for w in tagger(line):
            pos = getattr(w.feature, "pos1", "")
            surface = w.surface
            if pos in ("名詞", "固有名詞") and len(surface) >= 2 and surface not in STOP:
                counts[surface] = counts.get(surface, 0) + 1
    return [w for w, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]]


def suggest(args) -> int:
    project = Path(args.project)
    lines, video = project_text(project)
    chapters = video.get("chapters") or {}
    titles = [c.get("title") or c.get("label") or "" for c in chapters.values()]
    words = keywords(lines)

    doc = {
        "name": "underlay",
        "prompt": DEFAULT_PROMPT,
        "mood": ["calm", "curious", "unease"],
        "duration": 90,
        "segment_s": 30,
        "seeds": "auto",
        "crossfade_s": 2.5,
        "level_gain_db": 8.0,
        "level_limit": 0.95,
        "provider_settings": {"tokens": 1500, "guidance_scale": 3.0},
        "mix": DEFAULT_MIX,
    }
    text = yaml.safe_dump(doc, allow_unicode=True, sort_keys=False)
    out = Path(args.out) if args.out else None
    if out and out.exists() and not args.force:
        raise SystemExit(f"既にある: {out}（作り直すなら --force）")
    header = [
        "# bgm.yaml の下書き。engine/bgm.py suggest が台本から作った。",
        "# prompt は MusicGen 用の英語。話の内容に合わせて書き直すこと。",
    ]
    if titles:
        header.append(f"# 章: {' / '.join(t for t in titles if t)}")
    if words:
        header.append(f"# よく出る語: {' / '.join(words)}")
    body = "\n".join(header) + "\n" + text
    if out:
        out.write_text(body, encoding="utf-8")
        print(f"書いた: {out}")
    else:
        print(body, end="")
    return 0


def auto_seeds(prompt: str, count: int) -> list[int]:
    seeds = []
    for i in range(count):
        digest = hashlib.sha1(f"{prompt}|{i}".encode("utf-8")).digest()
        seeds.append(int.from_bytes(digest[:4], "big") % (2**31 - 1))
    return seeds


def load_config(project: Path) -> dict:
    path = project / "bgm.yaml"
    if not path.exists():
        raise SystemExit(f"bgm.yaml が無い: {path}（先に suggest か手で書く）")
    return load_yaml(path)


def resolve_duration(cfg: dict, project: Path, stage: Path | None) -> float:
    value = cfg.get("duration", 90)
    if value != "auto":
        return float(value)
    for path in ((stage or project) / "mix.yaml", project / "mix.yaml"):
        if path.exists():
            mix = load_yaml(path)
            if mix.get("duration"):
                return float(mix["duration"])
    return 90.0


# assemble.py の tile_bed は Python の wave で読む。float32（format 3）は読めないので、
# 書き出しは PCM 16 bit に固定する。
WAV_SUBTYPE = "PCM_16"


def signature(cfg: dict, duration: float, seeds: list[int]) -> str:
    payload = {
        "prompt": cfg.get("prompt", ""),
        "subtype": WAV_SUBTYPE,
        "segment_s": float(cfg.get("segment_s", 30)),
        "seeds": seeds,
        "crossfade_s": float(cfg.get("crossfade_s", 2.5)),
        "level_gain_db": float(cfg.get("level_gain_db", 8.0)),
        "level_limit": float(cfg.get("level_limit", 0.95)),
        "provider": cfg.get("provider", "musicgen"),
        "provider_settings": cfg.get("provider_settings") or {},
        "duration": round(duration, 2),
    }
    return hashlib.sha1(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]


def plan(cfg: dict, project: Path, stage: Path | None) -> dict:
    duration = resolve_duration(cfg, project, stage)
    segment_s = float(cfg.get("segment_s", 30))
    if segment_s <= 0 or segment_s > 30:
        raise SystemExit("segment_s は 1〜30 秒（MusicGen の上限 30 秒）")
    count = max(1, math.ceil(duration / segment_s))
    seeds = cfg.get("seeds", "auto")
    if seeds in (None, "", "auto"):
        seeds = auto_seeds(cfg.get("prompt", ""), count)
    else:
        seeds = [int(s) for s in seeds]
        if len(seeds) < count:
            raise SystemExit(f"seeds が足りない（{count} 本に {len(seeds)} 個）")
        seeds = seeds[:count]
    return {
        "duration": duration,
        "segment_s": segment_s,
        "count": count,
        "seeds": seeds,
        "signature": signature(cfg, duration, seeds),
    }


def generate(args) -> int:
    project = Path(args.project)
    cfg = load_config(project)
    name = cfg.get("name") or "underlay"
    assets = Path(args.assets).resolve() if args.assets else project / "assets"
    out_dir = assets / "bgm"
    wav_path = out_dir / f"{name}.wav"
    params_path = out_dir / f"{name}.params.yaml"
    p = plan(cfg, project, None)

    print(f"prompt: {cfg.get('prompt', '')}")
    print(f"seeds: {p['seeds']}")
    print(f"{p['count']} 本 × {p['segment_s']:g} 秒 / クロスフェード {float(cfg.get('crossfade_s', 2.5)):g} 秒")
    print(f"out: {wav_path}")
    if args.dry_run:
        print("（--dry-run: 生成しない）")
        return 0

    if wav_path.exists() and params_path.exists() and not args.force:
        old = load_yaml(params_path)
        if old.get("input_sha1") == p["signature"]:
            print("入力が変わっていない。飛ばす（作り直すなら --force）")
            return 0

    sal = sal_root()
    if str(sal) not in sys.path:
        sys.path.insert(0, str(sal))
    from semantic_audio_loom.engine import AudioAssetEngine
    from semantic_audio_loom.skills.sound import build_intent

    import numpy as np
    import soundfile as sf

    provider = cfg.get("provider") or "musicgen"
    engine = AudioAssetEngine(provider_name=provider, resolve_mode="rule", lang="ja")
    sound = {"role": "underscore", "mood": cfg.get("mood"), "prompt": cfg.get("prompt", "")}

    pieces = []
    settings = None
    sr = 0
    for i, seed in enumerate(p["seeds"]):
        print(f"  生成 {i + 1}/{p['count']}（seed {seed}）…", flush=True)
        sound_i = {**sound, "duration": p["segment_s"]}
        intent = build_intent("bgm", sound=sound_i, situation=cfg.get("situation", ""), seed=seed)
        asset = engine.generate(intent)
        pieces.append(np.asarray(asset.audio.wav, dtype=np.float32))
        sr = int(asset.audio.sample_rate)
        settings = asset.parameters.get("provider_settings") or settings

    if sr <= 0:
        raise SystemExit("生成した音のサンプルレートが読めない")
    # 生成ごとに sample_rate が違っても、最後の 1 本に合わせる（MusicGen は 32000、
    # 正規化後は config の出力形式）。最初の 1 本を基準にする。
    crossfade = float(cfg.get("crossfade_s", 2.5))
    out = pieces[0]
    for nxt in pieces[1:]:
        n = min(int(crossfade * sr), len(out), len(nxt))
        if n > 0:
            fade = np.linspace(0.0, 1.0, n, dtype=np.float32)
            out = out.copy()
            out[-n:] = out[-n:] * (1.0 - fade) + nxt[:n] * fade
        out = np.concatenate([out, nxt[n:]])

    gain = 10 ** (float(cfg.get("level_gain_db", 8.0)) / 20.0)
    out = out * gain
    limit = float(cfg.get("level_limit", 0.95))
    peak = float(np.max(np.abs(out))) if out.size else 0.0
    if peak > limit:
        out = out * (limit / peak)

    out_dir.mkdir(parents=True, exist_ok=True)
    sf.write(wav_path, out, sr, subtype=WAV_SUBTYPE)
    duration = round(len(out) / sr, 3)
    params = {
        "name": name,
        "metadata": {
            "asset_type": "bgm",
            "prompt": cfg.get("prompt", ""),
            "provider": provider,
            "sample_rate": sr,
            "channels": 1 if out.ndim == 1 else int(out.shape[1]),
            "duration": duration,
            "seeds": p["seeds"],
            "crossfade_s": crossfade,
            "level": f"+{float(cfg.get('level_gain_db', 8.0)):g} dB、ピークを {limit:g} でリミット",
        },
        "parameters": {
            "version": 3,
            "asset_type": "bgm",
            "provider": provider,
            "spec": {
                "duration": p["segment_s"],
                "prompt": cfg.get("prompt", ""),
                "mood": cfg.get("mood"),
            },
            "seeds": p["seeds"],
            "crossfade_s": crossfade,
            "level_gain_db": float(cfg.get("level_gain_db", 8.0)),
            "level_limit": limit,
            "duration": duration,
            "sample_rate": sr,
            "provider_settings": settings or cfg.get("provider_settings") or {},
        },
        "input_sha1": p["signature"],
    }
    with open(params_path, "w", encoding="utf-8") as f:
        f.write("# engine/bgm.py generate が書く（入力が変わると作り直す）\n")
        yaml.safe_dump(params, f, allow_unicode=True, sort_keys=False)
    print(f"書いた: {wav_path}（{duration:.2f} 秒）")
    print(f"書いた: {params_path}")
    return 0


def mix(args) -> int:
    project = Path(args.project)
    cfg = load_config(project)
    name = cfg.get("name") or "underlay"
    stage = Path(args.stage).resolve() if args.stage else None
    mix_path = (stage or project) / "mix.yaml"
    if not mix_path.exists():
        raise SystemExit(f"mix.yaml が無い: {mix_path}（先に assemble.py --no-render）")
    spec = load_yaml(mix_path)
    mix_cfg = cfg.get("mix") or DEFAULT_MIX

    beds = 0
    for stem in spec.get("stems", []):
        if stem.get("role") == "bed":
            stem["gain_db"] = float(mix_cfg.get("gain_db", DEFAULT_MIX["gain_db"]))
            beds += 1
    if not beds:
        raise SystemExit(f"mix.yaml に bed が無い: {mix_path}")
    spec["duck"] = {
        **DEFAULT_MIX["duck"],
        **(mix_cfg.get("duck") or {}),
    }
    if args.dry_run:
        print(f"bed {beds} 本を gain {mix_cfg.get('gain_db', DEFAULT_MIX['gain_db'])} dB / "
              f"duck {spec['duck']} で混ぜる（--dry-run: 書かない）")
        return 0
    with open(mix_path, "w", encoding="utf-8") as f:
        f.write("# assemble.py が書き、engine/bgm.py mix が bed と duck を直した\n")
        yaml.safe_dump(spec, f, allow_unicode=True, sort_keys=False)

    assets = Path(args.assets).resolve() if args.assets else project / "assets"
    out_dir = assets / "renders"
    out_dir.mkdir(parents=True, exist_ok=True)
    sal = sal_root()
    # 出力名は assemble.py が mix.yaml に書いた `output`（= 作品名）。
    # export_timeline.py は assets/renders/<作品名>.wav を読む。
    mix_name = spec.get("output") or (stage or project).name
    cmd = [
        sys.executable, str(sal / "bin" / "mix.py"),
        "--file", str(mix_path), "--out-dir", str(out_dir), "--name", mix_name,
    ]
    print("+ " + " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=sal, env={**os.environ, "PYTHONPATH": str(sal)})
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="台本に合わせた敷き音を作り、ミックスへ反映する。")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("suggest", help="bgm.yaml の下書きを出す")
    p.add_argument("--project", required=True)
    p.add_argument("--out", default="")
    p.add_argument("--force", action="store_true")

    p = sub.add_parser("generate", help="bgm.yaml から underlay.wav を作る")
    p.add_argument("--project", required=True)
    p.add_argument("--assets", default="")
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("mix", help="mix.yaml の bed と duck を直して混ぜる")
    p.add_argument("--project", required=True)
    p.add_argument("--stage", default="")
    p.add_argument("--assets", default="")
    p.add_argument("--dry-run", action="store_true")

    args = ap.parse_args()
    if args.cmd == "suggest":
        return suggest(args)
    if args.cmd == "generate":
        return generate(args)
    return mix(args)


if __name__ == "__main__":
    sys.exit(main())
