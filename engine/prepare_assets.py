#!/usr/bin/env python3
"""キャストの表情シートから、描画用の素材を作る。

作るもの（--out の下）:
  <id>_<expr>.png / _m1.png / _m0.png   口の 3 状態（閉・半開・開）
  <id>_<expr>.png                       口パクをしない側は 1 枚だけ
  faces.json                            感情→表情の対応表、画像の並び、口の錨

  engine/prepare_assets.py --cast casts/mirai-mirabo.cast.yaml --out build/cyber-basics/assets

シートは 4列×2行 = 8マス。左から右、上の行が先。並び順はキャストが書く。

方針（絵から測る。座標を手で書かない）:
- **背景は透過で返ってくる前提。** 白を抜かない。アルファをそのまま使う。
- 8マスは、絵の外接矩形の上端と横中心でそろえる（目分量のズレを吸収する）。
- 口パクをする側は、**口を消さない**。元の唇の線を 1 マスずつ拾い、その線の**下に
  口の中を描き足す**。唇の線はそのまま残るので、開いても顔の線は崩れない。
  線の位置は絵から測るので、マスごとに口の位置が違ってもずれない。
- 口パクをしない側は、表情の差し替えだけ。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import yaml
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
TOP_MARGIN = 6
COLUMNS, ROWS = 4, 2


def cells(sheet: Path) -> list[Image.Image]:
    im = Image.open(sheet).convert("RGBA")
    cw, ch = im.width / COLUMNS, im.height / ROWS
    out = []
    for r in range(ROWS):
        for c in range(COLUMNS):
            x0, y0 = int(round(c * cw)), int(round(r * ch))
            x1, y1 = int(round((c + 1) * cw)), int(round((r + 1) * ch))
            out.append(im.crop((x0, y0, x1, y1)))
    return out


def normalize(cell: Image.Image, canvas: tuple[int, int]) -> Image.Image:
    """外接矩形の上端を TOP_MARGIN に、横中心を画布の中心に置く。"""
    a = np.array(cell)
    ys, xs = np.nonzero(a[..., 3] > 32)
    if len(ys) == 0:
        raise RuntimeError("空のマスがある")
    cx = (xs.min() + xs.max()) / 2
    w, h = canvas
    dx = int(round(w / 2 - cx))
    dy = int(round(TOP_MARGIN - ys.min()))
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(cell, (dx, dy))
    return out


def eye_center(rgb: np.ndarray, alpha: np.ndarray) -> tuple[float, float] | None:
    """両目の虹彩のあいだの点。閉じた目は、まつ毛の線で代用する。"""
    r, g, b = rgb[..., 0].astype(np.int16), rgb[..., 1].astype(np.int16), rgb[..., 2].astype(np.int16)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    ys, xs = np.nonzero(alpha > 32)
    top, h = ys.min(), ys.max() - ys.min()
    band = np.zeros_like(alpha, bool)
    band[top + int(h * 0.20):top + int(h * 0.50)] = True
    dark = (b > r + 12) & (lum < 150) & (alpha > 32) & band
    dark = ndimage.binary_closing(dark, iterations=2)
    lab, n = ndimage.label(dark)
    if n == 0:
        return None
    sizes = ndimage.sum(dark, lab, range(1, n + 1))
    for lo, hi, hmax in ((150, 1800, 999), (40, 1800, 14)):
        comps = []
        for k in range(1, n + 1):
            if not (lo <= sizes[k - 1] <= hi):
                continue
            yy, xx = np.nonzero(lab == k)
            if yy.max() - yy.min() + 1 > hmax:
                continue
            if not (90 <= xx.mean() <= 330):
                continue
            comps.append((float(xx.mean()), float(yy.mean())))
        if len(comps) >= 2:
            comps.sort()
            L, R = comps[0], comps[-1]
            return ((L[0] + R[0]) / 2, (L[1] + R[1]) / 2)
    return None


def lip_line(rgb: np.ndarray, pt: tuple[float, float],
             box: tuple[int, int, int]) -> tuple[int, int, int, np.ndarray] | None:
    """口の線の上端を列ごとに拾う。返り値は (x0, 左端, 右端, 列ごとの y)。"""
    mx, my = int(round(pt[0])), int(round(pt[1]))
    half, up, dn = box
    x0, x1 = max(0, mx - half), min(rgb.shape[1], mx + half)
    y0, y1 = max(0, my - up), min(rgb.shape[0], my + dn)
    sub = rgb[y0:y1, x0:x1]
    lum = 0.299 * sub[..., 0] + 0.587 * sub[..., 1] + 0.114 * sub[..., 2]
    n = sub.shape[1]
    top = np.full(n, np.nan)
    for x in range(n):
        col = lum[:, x]
        if col.min() < 228:
            top[x] = y0 + int(np.argmin(col))
    idx = np.nonzero(~np.isnan(top))[0]
    if len(idx) < 6:
        return None
    lo, hi = int(idx.min()), int(idx.max())
    tt = np.interp(np.arange(n), idx, top[idx])
    tt = ndimage.gaussian_filter1d(tt, 1.2)
    return x0, lo, hi, tt


def add_mouth(base: Image.Image, line: tuple, depth: float,
              color: tuple[int, int, int]) -> Image.Image:
    """唇の線の下に、口の中を描き足す。線は残す。"""
    a = np.array(base).astype(np.float32)
    x0, lo, hi, tt = line
    h, w = a.shape[:2]
    shape = np.zeros((h, w), np.float32)
    cx = (lo + hi) / 2
    rx = (hi - lo) / 2 + 0.5
    for x in range(lo, hi + 1):
        t = (x - cx) / rx
        d = depth * max(0.0, 1 - t * t) ** 0.55
        y = int(round(tt[x] + 1))
        if d <= 0 or y >= h:
            continue
        shape[y:min(h, y + int(round(d)) + 1), x0 + x] = 1.0
    m = ndimage.gaussian_filter(shape, 0.75)[..., None] * 0.88
    out = a.copy()
    out[..., :3] = a[..., :3] * (1 - m) + np.array(color, np.float32) * m
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def make(base: Image.Image, pt: tuple[float, float], mouth: dict) -> tuple[list[Image.Image], dict]:
    rgb = np.array(base)[..., :3].astype(np.float32)
    line = lip_line(rgb, pt, tuple(mouth["box"]))
    if line is None:
        raise RuntimeError(f"口の線が見つからない {pt}")
    imgs = [add_mouth(base, line, mouth["drop"] * k, tuple(mouth["inner"]))
            for _, k in OPENNESS]
    meta = {"line_span": [int(line[0] + line[1]), int(line[0] + line[2])],
            "line_y": [float(np.min(line[3][line[1]:line[2] + 1])),
                       float(np.max(line[3][line[1]:line[2] + 1]))]}
    return imgs, meta


OPENNESS: list = []


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default="", help="作品の置き場（video.yaml の親）")
    ap.add_argument("--cast", default="", help="キャストの名。既定は video.yaml の cast")
    ap.add_argument("--out", required=True, help="素材の書き先（例: build/<work>/assets）")
    ap.add_argument("--sheets", default=str(REPO / "sheets"), help="表情シートの置き場")
    args = ap.parse_args()

    name = args.cast
    if not name:
        if not args.work:
            ap.error("--cast か --work が要る")
        vpath = Path(args.work) / "video.yaml"
        if not vpath.exists():
            ap.error(f"video.yaml が無い: {vpath}")
        with open(vpath, encoding="utf-8") as f:
            name = (yaml.safe_load(f) or {}).get("cast", "")
        if not name:
            ap.error(f"video.yaml に cast が無い: {vpath}")
    cast_path = REPO / "casts" / f"{name}.cast.yaml"

    global OPENNESS
    with open(cast_path, encoding="utf-8") as f:
        cast = yaml.safe_load(f)
    OPENNESS = [(str(t), float(k)) for t, k in cast.get("mouth_states", [["m0", 1.0], ["m1", 0.42]])]

    sheets = Path(args.sheets)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    meta: dict = {"states": ["open", "half", "closed"], "by_emotion": {}, "blink": {},
                  "expressions": {}, "lip": {}}
    for ch in cast["characters"]:
        cid = ch["id"]
        path = sheets / ch["sheet"]
        if not path.exists():
            raise SystemExit(f"表情シートが無い: {path}\n  → sheets/README.md を見て置く")
        cs = cells(path)
        if len(cs) != COLUMNS * ROWS:
            raise RuntimeError(f"{cid}: {COLUMNS * ROWS}マスでない（{len(cs)}）")
        canvas = tuple(ch["canvas"])
        lip = bool(ch.get("lip", False))

        pt = None
        if lip:
            # 口の錨は **8マス共通で1本**。シートは「全マス同じ位置」が約束なので、
            # マスごとの測定値はノイズでしかない（目線が上へ行く表情は 20px ずれる）。
            found = []
            for cell in cs:
                b = np.array(normalize(cell, canvas))
                e = eye_center(b[..., :3], b[..., 3])
                if e:
                    found.append(e)
            if len(found) < 3:
                raise RuntimeError(f"{cid}: 目が3マスも見つからない")
            mx = float(np.median([e[0] for e in found]))
            my = float(np.median([e[1] for e in found]))
            keep = [e for e in found if abs(e[0] - mx) < 10 and abs(e[1] - my) < 10]
            if len(keep) >= 2:
                mx = float(np.median([e[0] for e in keep]))
                my = float(np.median([e[1] for e in keep]))
            ox, oy = ch.get("mouth_offset", [4.0, 66.0])
            pt = (mx + float(ox), my + float(oy))

        faces = {}
        for expr, cell in zip(ch["expressions"], cs):
            base = normalize(cell, canvas)
            base.save(out / f"{cid}_{expr}.png")
            files = [f"{cid}_{expr}_m0.png", f"{cid}_{expr}_m1.png", f"{cid}_{expr}.png"]
            if not lip:
                files = [f"{cid}_{expr}.png"] * 3
                faces[expr] = {"files": files}
                print(f"  {cid}/{expr}: 表情のみ")
                continue
            if pt is None:
                raise RuntimeError("目の錨を作れない")
            variants, info = make(base, pt, ch["mouth"])
            for (tag, _), im in zip(OPENNESS, variants):
                im.save(out / f"{cid}_{expr}_{tag}.png")
            faces[expr] = {"pt": [round(pt[0], 1), round(pt[1], 1)],
                           "files": files, **info}
            print(f"  {cid}/{expr}: pt={tuple(round(v, 1) for v in pt)} "
                  f"線 x={info['line_span']} y={[round(v) for v in info['line_y']]}")

        meta["by_emotion"][cid] = ch.get("by_emotion", {}) or {}
        meta["blink"][cid] = ch.get("blink", {}) or {}
        meta["expressions"][cid] = ch["expressions"]
        meta["lip"][cid] = lip
        meta[cid] = {"canvas": list(canvas), "faces": faces}

    (out / "faces.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print(f"faces.json を書いた: {out / 'faces.json'}")


if __name__ == "__main__":
    main()
