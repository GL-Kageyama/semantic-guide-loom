#!/usr/bin/env python3
"""掛け合い・胸像型（dialogue-bust）。

左に人、右に相棒、中央に章の札、下に字幕、最下部に進捗。
数字はすべて template.yaml から来る。ここに書くのは**並べ方**だけ。
"""
from __future__ import annotations

import math

from PIL import Image, ImageDraw, ImageFilter

import common as K


def make_bg(w: int, h: int) -> Image.Image:
    bg = K.TPL["background"]
    top = K.np.array(K.C("bg_top"), dtype=K.np.float32)
    bot = K.np.array(K.C("bg_bottom"), dtype=K.np.float32)
    ramp = K.np.linspace(0, 1, h, dtype=K.np.float32)[:, None, None]
    arr = K.np.broadcast_to(top, (h, w, 3)) * (1 - ramp) + bot * ramp
    arr = arr.astype(K.np.uint8).copy()
    im = Image.fromarray(arr)
    d = ImageDraw.Draw(im, "RGBA")
    # 点格子
    step, size = K.S(bg["dot_step"]), K.S(bg["dot_size"])
    dot = K.rgba(bg["dot_color"])
    for y in range(step, h, step):
        for x in range(step, w, step):
            d.ellipse([x, y, x + size, y + size], fill=dot)
    # 中央のほのかな光
    g = bg["glow"]
    gx0, gy0, gx1, gy1 = g["box"]
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([w * gx0, h * gy0, w * gx1, h * gy1], fill=K.rgba(g["color"]))
    glow = glow.filter(ImageFilter.GaussianBlur(K.S(g["blur"])))
    im = Image.alpha_composite(im.convert("RGBA"), glow)
    return im.convert("RGB")


def make_panel(ch: dict, idx: int, total: int, w: int, h: int) -> Image.Image:
    """中央の章の札。1 章ぶんを 1 枚に焼く。"""
    p = K.TPL["panel"]
    x0, y0, x1, y1 = (K.S(v) for v in p["box"])
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x0, y0, x1, y1], radius=K.S(p["radius"]), fill=K.C("panel_fill"),
                        outline=K.C("panel_line"), width=K.S(p["outline_width"]))
    pad = K.S(p["pad"])
    y = y0 + pad
    d.text((x0 + pad, y), ch["label"], font=K.font(p["label"]["size"], p["label"]["bold"]),
           fill=K.C("accent"))
    tag = f"{idx + 1} / {total}"
    tfnt = K.font(p["tag"]["size"])
    d.text((x1 - pad - tfnt.getlength(tag), y + K.S(p["tag"]["dy"])), tag, font=tfnt,
           fill=K.C("panel_tag"))
    y += K.S(p["rule_dy"])
    d.line([x0 + pad, y, x1 - pad, y], fill=K.C("panel_rule"), width=K.S(p["outline_width"]))
    y += K.S(p["after_rule_dy"])
    # ことば（大きく）
    term = K.text_img([ch["term"]], K.font(p["term"]["size"], p["term"]["bold"]), K.C("ink"),
                      K.S(0), align="left")
    im.alpha_composite(term, (x0 + pad - K.S(4), y))
    y += term.height + K.S(p["after_term_dy"])
    tf = K.font(p["title"]["size"], p["title"]["bold"])
    for line in K.wrap_jp(ch["title"], tf, x1 - x0 - pad * 2):
        t = K.text_img([line], tf, K.C("warm"), 0, align="left")
        im.alpha_composite(t, (x0 + pad - K.S(4), y))
        y += K.S(p["title"]["step"])
    y += K.S(p["after_title_dy"])
    sr = p["short_rule"]
    d.line([x0 + pad, y, x0 + pad + K.S(sr["width"]), y],
           fill=K.rgba(sr["color"]), width=K.S(sr["thickness"]))
    y += K.S(p["after_short_dy"])
    kf = K.font(p["key"]["size"])
    key_lines: list[str] = []
    for seg in ch["key"].split("\n"):
        key_lines += K.wrap_balanced(seg, kf, x1 - x0 - pad * 2)
    for line in key_lines:
        t = K.text_img([line], kf, K.C("pale"), 0, align="left")
        im.alpha_composite(t, (x0 + pad - K.S(4), y))
        y += K.S(p["key"]["step"])
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


def build(tl: dict, cast: K.Cast, fps: int, W: int, H: int):
    timing = K.TPL["timing"]
    bg = make_bg(W, H)
    panels = [make_panel(ch, ch["index"], len(tl["chapters"]), W, H)
              for ch in tl["chapters"]]
    subs = {c["name"]: make_subtitle(c["text"]) for c in tl["cues"] if c["text"]}

    # 口の列（口パクをする側だけ）
    thresh = [float(K.TPL["mouth"]["open_db"]), float(K.TPL["mouth"]["half_db"])]
    total_frames = int(round(tl["duration"] * fps))
    tracks = {
        c["name"]: K.mouth_track(c["wav"], c["start"], c["end"], fps, total_frames, thresh)
        for c in tl["cues"] if cast.lip(c["character"])
    }

    def face_at(char: str, t: float) -> str:
        """その人が最後に話した cue の表情を、次に話すまで保つ。"""
        cur = None
        for c in tl["cues"]:
            if c["start"] > t:
                break
            if c["character"] == char:
                cur = c
        return cast.face_for(char, cur)

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

    def offset(char: str, t: float) -> tuple[int, int]:
        """キャストの sin 波を、x と y に畳む。"""
        dx = dy = 0
        for m in cast.chars[char].get("motion") or []:
            v = int(round(math.sin(t * float(m["hz"]) + float(m.get("phase", 0.0)))
                          * K.S(float(m["amp"]))))
            if m.get("axis", "y") == "x":
                dx += v
            else:
                dy += v
        return dx, dy

    def draw_frame(t: float, fi: int) -> Image.Image:
        im = bg.copy()
        ch_idx = chapter_idx_at(t)
        if ch_idx >= 0:
            p = panels[ch_idx]
            slide = K.S(10) * max(0.0, 1.0 - (t - tl["chapters"][ch_idx]["start"])
                                  / timing["chapter_slide"])
            im.paste(p, (0, int(slide)), p)

        cur = cue_at(t)
        speaker = (cur["character"] if cur and t <= cur["end"] + timing["speaker_tail"]
                   else None)
        fi_t = min(total_frames - 1, int(t * fps))
        lvl = (int(tracks[cur["name"]][fi_t])
               if cur and cur["name"] in tracks else 2)

        for cid in cast.order:
            ch = cast.chars[cid]
            ox, oy = (K.S(v) for v in K.TPL["slots"][ch["slot"]]["origin"])
            dx, dy = offset(cid, t)
            fig = cast.sheet(cid, face_at(cid, t))[0 if speaker in (None, cid) else 1][lvl]
            im.paste(fig, (ox + dx, oy + dy), fig)

        # 字幕（発話の間だけ）
        if cur and cur["text"] and (cur["start"] - timing["subtitle_lead"] <= t
                                    <= cur["end"] + timing["subtitle_tail"]):
            s = subs[cur["name"]]
            im.paste(s, ((W - s.width) // 2, K.S(K.TPL["subtitle"]["y"])), s)

        # 上段
        hd = K.TPL["header"]
        d = ImageDraw.Draw(im, "RGBA")
        d.text((K.S(hd["title"]["x"]), K.S(hd["title"]["y"])), tl["title"],
               font=K.font(hd["title"]["size"], hd["title"]["bold"]), fill=K.C("ink"))
        ch_label = ""
        if ch_idx >= 0:
            ch = tl["chapters"][ch_idx]
            ch_label = f"{ch['label']}  {ch['title']}"
        if ch_label:
            d.text((K.S(hd["chapter"]["x"]), K.S(hd["chapter"]["y"])), ch_label,
                   font=K.font(hd["chapter"]["size"]), fill=K.C("header_sub"))
        tag = tl["channel"]
        cf = K.font(hd["channel"]["size"])
        d.text((W - K.S(hd["channel"]["right"]) - cf.getlength(tag), K.S(hd["channel"]["y"])),
               tag, font=cf, fill=K.C("accent"))
        d.line([K.S(hd["title"]["x"]), K.S(hd["rule_y"]),
                W - K.S(hd["title"]["x"]), K.S(hd["rule_y"])],
               fill=K.rgba(hd["rule_color"]), width=K.S(hd["rule_width"]))

        K.progress_bar(im, t, tl, W, H)
        return im

    return draw_frame
