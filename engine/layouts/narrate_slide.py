#!/usr/bin/env python3
"""語り・スライド型（narrate-slide）。

人物は置かない。左に章の題と箇条書き、下に語りの字幕、最下部に進捗。
社内の説明・研修のように「読み物として立つ画面」を作る型。

dialogue-bust との違いは 3 つだけ——背景に点格子を敷かない、キャストを取らない、
章が「札」ではなく「スライド」になる（`chapters` の `bullets` を読む）。
"""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFilter

import common as K


def make_bg(w: int, h: int) -> Image.Image:
    bg = K.TPL["background"]
    top = K.np.array(K.C("bg_top"), dtype=K.np.float32)
    bot = K.np.array(K.C("bg_bottom"), dtype=K.np.float32)
    ramp = K.np.linspace(0, 1, h, dtype=K.np.float32)[:, None, None]
    arr = K.np.broadcast_to(top, (h, w, 3)) * (1 - ramp) + bot * ramp
    im = Image.fromarray(arr.astype(K.np.uint8).copy())
    # 左端の縦の帯（題の欄）
    band = K.TPL["accent_band"]
    d = ImageDraw.Draw(im, "RGBA")
    d.rectangle([0, 0, K.S(band["width"]), h], fill=K.rgba(band["color"]))
    if bg.get("glow"):
        g = bg["glow"]
        gx0, gy0, gx1, gy1 = g["box"]
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse([w * gx0, h * gy0, w * gx1, h * gy1],
                                     fill=K.rgba(g["color"]))
        im = Image.alpha_composite(im.convert("RGBA"),
                                   glow.filter(ImageFilter.GaussianBlur(K.S(g["blur"]))))
        im = im.convert("RGB")
    return im


def make_slide(ch: dict, idx: int, total: int, w: int, h: int) -> Image.Image:
    """章 1 つぶんのスライド。文字だけを透明の板に焼く（背景は別）。"""
    p = K.TPL["slide"]
    x = K.S(p["x"])
    cw = K.S(p["content_width"])
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    # 右奥に章の番号を薄く置く（会議の画面でも、いま何章かが遠目に分かる）
    num = f"{idx + 1:02d}"
    nf = K.font(p["number"]["size"], True)
    nbox = K.text_img([num], nf, K.C("accent"), 0, align="left")
    nbox.putalpha(nbox.getchannel("A").point(lambda v: int(v * p["number"]["alpha"])))
    im.alpha_composite(nbox, (w - K.S(p["number"]["right"]) - nbox.width,
                              K.S(p["number"]["y"])))

    y = K.S(p["label_y"])
    d.text((x, y), ch["label"], font=K.font(p["label"]["size"], True), fill=K.C("accent"))
    y = K.S(p["title_y"])
    tf = K.font(p["title"]["size"], True)
    for line in K.wrap_jp(ch["title"], tf, cw):
        t = K.text_img([line], tf, K.C("ink"), 0, align="left")
        im.alpha_composite(t, (x - K.S(4), y))
        y += K.S(p["title"]["step"])
    y += K.S(p["after_title_dy"])
    sr = p["rule"]
    d.line([x, y, x + K.S(sr["width"]), y], fill=K.rgba(sr["color"]),
           width=K.S(sr["thickness"]))
    y = K.S(p["bullets_y"])

    bf = K.font(p["bullet"]["size"])
    mk = p["bullet"]["marker"]
    for item in ch.get("bullets") or []:
        lines = K.wrap_jp(item, bf, cw - K.S(p["bullet"]["indent"]))
        d.rectangle([x, y + K.S(mk["dy"]), x + K.S(mk["size"]), y + K.S(mk["dy"]) + K.S(mk["size"])],
                    fill=K.C("accent"))
        for j, line in enumerate(lines):
            t = K.text_img([line], bf, K.C("pale"), 0, align="left")
            im.alpha_composite(t, (x + K.S(p["bullet"]["indent"]), y))
            y += K.S(p["bullet"]["step"])
        y += K.S(p["bullet"]["gap"])
    return im


def make_subtitle(text: str) -> Image.Image:
    s = K.TPL["subtitle"]
    fnt = K.font(s["size"])
    max_w = K.S(s["max_width"])
    lines = K.wrap_balanced(text, fnt, max_w)
    if len(lines) > int(s["max_lines"]):
        lines = K.wrap_jp(text, fnt, max_w)[:int(s["max_lines"]) + 1]
    body = K.text_img(lines, fnt, K.C("ink"), K.S(s["spacing"]), align="center",
                      shadow=K.C("subtitle_shadow"))
    pad = K.S(s["pad"])
    box_w = K.S(s["box_width"])
    im = Image.new("RGBA", (max(box_w, body.width + pad * 2), body.height + pad * 2),
                   (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=K.S(s["radius"]),
                        fill=K.C("subtitle_fill"))
    im.alpha_composite(body, ((im.width - body.width) // 2, pad))
    return im


def build(tl: dict, cast, fps: int, W: int, H: int):
    timing = K.TPL["timing"]
    bg = make_bg(W, H)
    slides = [make_slide(ch, ch["index"], len(tl["chapters"]), W, H)
              for ch in tl["chapters"]]
    subs = {c["name"]: make_subtitle(c["text"]) for c in tl["cues"] if c["text"]}

    def cue_at(t: float) -> dict | None:
        cur = None
        for c in tl["cues"]:
            if c["start"] - timing["subtitle_lead"] <= t:
                cur = c
            else:
                break
        return cur

    def chapter_idx_at(t: float) -> int:
        idx = -1
        for ch in tl["chapters"]:
            if t >= ch["start"]:
                idx = ch["index"]
        return idx

    def draw_frame(t: float, fi: int) -> Image.Image:
        im = bg.copy()
        ch_idx = chapter_idx_at(t)
        if ch_idx >= 0:
            p = slides[ch_idx]
            slide = K.S(12) * max(0.0, 1.0 - (t - tl["chapters"][ch_idx]["start"])
                                  / timing["chapter_slide"])
            im.paste(p, (0, int(slide)), p)

        cur = cue_at(t)
        if cur and cur["text"] and (cur["start"] - timing["subtitle_lead"] <= t
                                    <= cur["end"] + timing["subtitle_tail"]):
            s = subs[cur["name"]]
            im.paste(s, ((W - s.width) // 2, K.S(K.TPL["subtitle"]["y"])), s)

        hd = K.TPL["header"]
        d = ImageDraw.Draw(im, "RGBA")
        d.text((K.S(hd["title"]["x"]), K.S(hd["title"]["y"])), tl["title"],
               font=K.font(hd["title"]["size"], hd["title"]["bold"]), fill=K.C("header_sub"))
        tag = tl["channel"]
        cf = K.font(hd["channel"]["size"])
        if tag:
            d.text((W - K.S(hd["channel"]["right"]) - cf.getlength(tag),
                    K.S(hd["channel"]["y"])), tag, font=cf, fill=K.C("header_sub"))

        K.progress_bar(im, t, tl, W, H)
        return im

    return draw_frame
