#!/usr/bin/env python3
"""型に依らない道具。描く側（engine/layouts/）と、読み込む側（render.py）が共有する。

ここが持つのは 3 つだけ——**尺度**（720p を 1 として数える）、**色**（型のパレット）、
**書体**（型の 1 本）。型ごとに違うのは layouts/ の側。
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
REPO = HERE.parent

SCALE = 1.0
TPL: dict = {}
PAL: dict = {}
ASSETS = ""


def S(v: float) -> int:
    """720p 基準の数を、いまの画布の画素へ。"""
    return int(round(v * SCALE))


def C(name: str) -> tuple:
    """パレットの色。3 つでも 4 つでも通す。"""
    return tuple(int(v) for v in PAL[name])


def rgba(v) -> tuple:
    """型の YAML に直に書いた色（[r,g,b] / [r,g,b,a]）。"""
    return tuple(int(x) for x in v)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    f = TPL["font"]
    return ImageFont.truetype(f["path"], S(size), index=f["bold"] if bold else f["regular"])


def load_yaml(path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ── 声の包絡 ──────────────────────────────────────────────────────────────

def envelope(path: str, fps: int) -> np.ndarray:
    import wave
    with wave.open(path, "rb") as w:
        sr, ch = w.getframerate(), w.getnchannels()
        raw = w.readframes(w.getnframes())
    a = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    a = a.reshape(-1, ch).mean(axis=1)
    hop = sr / fps
    n = max(1, int(math.ceil(len(a) / hop)))
    out = np.zeros(n, dtype=np.float32)
    win = int(hop)
    for i in range(n):
        seg = a[int(i * hop): int(i * hop) + win]
        if len(seg):
            out[i] = float(np.sqrt((seg ** 2).mean()))
    return out


def mouth_track(path: str, start: float, end: float, fps: int, total: int,
                thresh: list[float]) -> np.ndarray:
    """3 状態の列（0=開 1=半開 2=閉）。声の大きさだけで決める。"""
    env = envelope(path, fps)
    db = 20.0 * np.log10(np.maximum(env, 1e-7))
    lvl = np.where(db > thresh[0], 0, np.where(db > thresh[1], 1, 2)).astype(np.int8)
    # 立ち上がりは速く、戻りは遅く（口は急に閉じない）
    for i in range(1, len(lvl)):
        if lvl[i] > lvl[i - 1]:
            lvl[i] = lvl[i - 1]
        elif lvl[i] > 1 and i > 1 and lvl[i - 1] == 0:
            lvl[i] = 1
    track = np.full(total, 2, dtype=np.int8)
    i0 = int(round(start * fps))
    i1 = min(total, int(round(end * fps)) + 1)
    j0 = 0
    for i in range(i0, i1):
        if j0 >= len(lvl):
            break
        track[i] = lvl[j0]
        j0 += 1
    return track


# ── 素材 ──────────────────────────────────────────────────────────────────

def _dim(im: Image.Image, k: float) -> Image.Image:
    r, g, b, a = im.split()
    f = lambda v: int(v * k)                       # noqa: E731
    return Image.merge("RGBA", (r.point(f), g.point(f), b.point(f), a))


class Cast:
    """表情シートから作った素材。1 表情あたり [開, 半開, 閉] の 3 枚を持つ。"""

    def __init__(self, spec: dict, dim: float) -> None:
        with open(os.path.join(ASSETS, "faces.json"), encoding="utf-8") as f:
            self.meta = json.load(f)
        self.spec = spec
        self.chars = {c["id"]: c for c in spec["characters"]}
        self.order = [c["id"] for c in spec["characters"]]
        self.default = spec.get("default_expression", "neutral")
        self.dim_k = dim
        self._cache: dict[tuple[str, str], tuple[list, list]] = {}

    def scale(self, char: str) -> float:
        return float(self.chars[char].get("scale", 1.0))

    def lip(self, char: str) -> bool:
        return bool(self.meta["lip"].get(char, False))

    def gain(self, char: str, face: str) -> float:
        """表情ごとの身体の揺れの倍率。未記載は 1.0。

        明示の face があるコマだけに掛ける（古い作品の揺れを変えないため）。
        """
        return float((self.chars[char].get("motion_gain") or {}).get(face, 1.0))

    def sheet(self, char: str, expr: str) -> tuple[list, list]:
        """(ふつう, 明度を落としたもの)。それぞれ 3 状態の画像。

        口パクをしない側は 3 状態が同じファイルなので、1 枚だけ開いて使い回す。
        """
        key = (char, expr)
        if key not in self._cache:
            files = self.meta[char]["faces"][expr]["files"]
            k = self.scale(char)
            raw: dict[str, tuple[Image.Image, Image.Image]] = {}
            for f in files:
                if f in raw:
                    continue
                im = Image.open(os.path.join(ASSETS, f)).convert("RGBA")
                if k != 1.0:
                    im = im.resize((int(round(im.width * k)), int(round(im.height * k))),
                                   Image.LANCZOS)
                raw[f] = (im, _dim(im, self.dim_k))
            self._cache[key] = ([raw[f][0] for f in files], [raw[f][1] for f in files])
        return self._cache[key]

    def face_for(self, char: str, cue: dict | None) -> str:
        faces = self.meta[char]["faces"]
        if cue is None:
            return self.default if self.default in faces else next(iter(faces))
        f = cue.get("face") or ""
        if f and f in faces:
            return f
        f = self.meta["by_emotion"].get(char, {}).get(cue.get("emotion", ""), self.default)
        return f if f in faces else self.default


# ── 文字 ──────────────────────────────────────────────────────────────────

NO_LINE_HEAD = set("、。，．！？）」』】…ー〜：；・")


def wrap_jp(text: str, fnt: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    lines: list[str] = []
    cur = ""
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        trial = cur + ch
        if fnt.getlength(trial) > max_w and cur:
            # 行頭に句読点を置かない
            if ch in NO_LINE_HEAD:
                cur = trial
                lines.append(cur)
                cur = ""
            else:
                lines.append(cur)
                cur = ch
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def wrap_balanced(text: str, fnt: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    """2 行に割るとき、行の長さを揃える。句読点の後ろを優先する。"""
    if fnt.getlength(text) <= max_w:
        return [text]
    best, best_score = None, None
    for k in range(1, len(text)):
        if text[k] in NO_LINE_HEAD:
            continue
        w1, w2 = fnt.getlength(text[:k]), fnt.getlength(text[k:])
        if w1 > max_w or w2 > max_w:
            continue
        score = abs(w1 - w2) - (S(60) if text[k - 1] in "、。！？" else 0)
        if best_score is None or score < best_score:
            best, best_score = k, score
    if best is None:
        return wrap_jp(text, fnt, max_w)
    return [text[:best], text[best:]]


def text_img(lines: list[str], fnt: ImageFont.FreeTypeFont, fill, spacing: int,
             align: str = "center", shadow=None) -> Image.Image:
    widths = [fnt.getlength(s) for s in lines]
    asc, desc = fnt.getmetrics()
    w = int(max(widths)) + S(8)
    h = (asc + desc) * len(lines) + spacing * (len(lines) - 1) + S(8)
    im = Image.new("RGBA", (max(1, w), max(1, h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = S(4)
    for s, sw in zip(lines, widths):
        x = (im.width - sw) / 2 if align == "center" else S(4)
        if shadow:
            d.text((x + S(2), y + S(2)), s, font=fnt, fill=shadow)
        d.text((x, y), s, font=fnt, fill=fill)
        y += asc + desc + spacing
    return im


def progress_bar(im: Image.Image, t: float, tl: dict, W: int, H: int) -> None:
    """最下部の帯と、章の目盛り。どの型でも同じ意味を持つ。"""
    pg = TPL["progress"]
    d = ImageDraw.Draw(im, "RGBA")
    prog = max(0.0, min(1.0, t / max(0.001, tl["duration"])))
    d.rectangle([0, H - S(pg["bar_height"]), W, H], fill=rgba(pg["track_color"]))
    d.rectangle([0, H - S(pg["bar_height"]), int(W * prog), H], fill=C("accent"))
    for ch in tl["chapters"]:
        x = int(W * min(1.0, ch["start"] / max(0.001, tl["duration"])))
        d.rectangle([x, H - S(pg["tick_height"]), x + S(pg["tick_width"]), H],
                    fill=rgba(pg["tick_color"]))
