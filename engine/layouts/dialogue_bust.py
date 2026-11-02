#!/usr/bin/env python3
"""掛け合い・胸像型（dialogue-bust）。

左に人、右に相棒、中央に章の札、下に字幕、最下部に進捗。
数字はすべて template.yaml から来る。ここに書くのは**並べ方**だけ。
"""
from __future__ import annotations

import bisect
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


def _header(ch: dict, idx: int, total: int, x0: int, y0: int, x1: int,
            im: Image.Image | None = None) -> int:
    """章のヘッダを描き、本文（key / 詳細）の開始 y を返す。

    `im=None` なら描かずに測るだけ。`text_img` は 8px の余白を足すので、
    測る側も同じ helper を通す（固定値を書かない）。
    """
    p = K.TPL["panel"]
    pad = K.S(p["pad"])
    d = ImageDraw.Draw(im) if im is not None else None
    y = y0 + pad
    if d is not None:
        d.text((x0 + pad, y), ch["label"],
               font=K.font(p["label"]["size"], p["label"]["bold"]),
               fill=K.C("accent"))
        tag = f"{idx + 1} / {total}"
        tfnt = K.font(p["tag"]["size"])
        d.text((x1 - pad - tfnt.getlength(tag), y + K.S(p["tag"]["dy"])), tag,
               font=tfnt, fill=K.C("panel_tag"))
    y += K.S(p["rule_dy"])
    if d is not None:
        d.line([x0 + pad, y, x1 - pad, y], fill=K.C("panel_rule"),
               width=K.S(p["outline_width"]))
    y += K.S(p["after_rule_dy"])
    # ことば（大きく）
    term = K.text_img([ch["term"]], K.font(p["term"]["size"], p["term"]["bold"]),
                      K.C("ink"), K.S(0), align="left")
    if im is not None:
        im.alpha_composite(term, (x0 + pad - K.S(4), y))
    y += term.height + K.S(p["after_term_dy"])
    tf = K.font(p["title"]["size"], p["title"]["bold"])
    for line in K.wrap_jp(ch["title"], tf, x1 - x0 - pad * 2):
        t = K.text_img([line], tf, K.C("warm"), 0, align="left")
        if im is not None:
            im.alpha_composite(t, (x0 + pad - K.S(4), y))
        y += K.S(p["title"]["step"])
    y += K.S(p["after_title_dy"])
    sr = p["short_rule"]
    if d is not None:
        d.line([x0 + pad, y, x0 + pad + K.S(sr["width"]), y],
               fill=K.rgba(sr["color"]), width=K.S(sr["thickness"]))
    y += K.S(p["after_short_dy"])
    return y


def detail_geometry(ch: dict) -> dict:
    """章題の行数から、詳細カードの本文開始と容量を出す。

    `dialogue_bust` の `panel.detail` が無い型では呼ばない。
    """
    p = K.TPL["panel"]
    detail = p.get("detail")
    if not detail:
        raise ValueError("panel.detail が型に無い")
    x0, y0, x1, y1 = (K.S(v) for v in p["box"])
    body_top = _header(ch, 0, 1, x0, y0, x1)
    pad = K.S(p["pad"])
    head_cfg = detail["head"]
    line_cfg = detail["line"]
    head_font = K.font(head_cfg["size"], head_cfg.get("bold", False))
    line_font = K.font(line_cfg["size"], line_cfg.get("bold", False))
    head_h = sum(head_font.getmetrics())
    line_h = sum(line_font.getmetrics())
    gap = K.S(detail.get("head_gap", 6))
    step = K.S(line_cfg["step"])
    bottom = y1 - pad
    first_line = body_top + head_h + gap
    computed = (0 if bottom < first_line + line_h
                else (bottom - first_line - line_h) // step + 1)
    capacity = min(int(detail.get("max_lines", computed)), computed)
    return {
        "body_top": body_top,
        "bottom": bottom,
        "capacity": max(0, capacity),
        "inner_width": x1 - x0 - pad * 2,
        "head_font": head_font,
        "line_font": line_font,
        "head_h": head_h,
        "line_h": line_h,
        "step": step,
    }


def make_panel(ch: dict, idx: int, total: int, w: int, h: int,
               card: dict | None = None) -> Image.Image:
    """中央の章の札。1 章ぶん（または詳細カード 1 枚）を焼く。"""
    p = K.TPL["panel"]
    x0, y0, x1, y1 = (K.S(v) for v in p["box"])
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x0, y0, x1, y1], radius=K.S(p["radius"]), fill=K.C("panel_fill"),
                        outline=K.C("panel_line"), width=K.S(p["outline_width"]))
    pad = K.S(p["pad"])
    y = _header(ch, idx, total, x0, y0, x1, im)
    if card is not None:
        detail = p["detail"]
        hf = K.font(detail["head"]["size"], detail["head"].get("bold", False))
        lf = K.font(detail["line"]["size"], detail["line"].get("bold", False))
        d.text((x0 + pad, y), card["head"], font=hf, fill=K.C("warm"))
        y += sum(hf.getmetrics()) + K.S(detail.get("head_gap", 6))
        for line in card["lines"]:
            d.text((x0 + pad, y), line, font=lf, fill=K.C("ink"))
            y += K.S(detail["line"]["step"])
        return im
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


def _validate_card(ch: dict, card: dict, geo: dict) -> None:
    tag = f"{ch.get('cue', '?')} / {card.get('cue', '?')}"
    head = card.get("head")
    if not isinstance(head, str) or not head or "\n" in head:
        raise ValueError(f"{tag}: 詳細カードの head が空か、改行を含む")
    lines = card.get("lines")
    if not isinstance(lines, list) or not lines:
        raise ValueError(f"{tag}: 詳細カードの lines が空")
    if len(lines) > geo["capacity"]:
        raise ValueError(
            f"{tag}: 詳細カードが {len(lines)} 行（容量 {geo['capacity']} 行）"
        )
    if "warm" not in K.PAL or "ink" not in K.PAL:
        raise ValueError(f"{tag}: palette に warm / ink が無い")
    if geo["head_font"].getlength(head) > geo["inner_width"]:
        raise ValueError(f"{tag}: head が 1 行に収まらない（{head!r}）")
    for line in lines:
        if not isinstance(line, str) or not line or "\n" in line:
            raise ValueError(f"{tag}: lines に空文字か改行がある")
        if geo["line_font"].getlength(line) > geo["inner_width"]:
            raise ValueError(
                f"{tag}: 行が内側 {geo['inner_width']}px に収まらない（{line!r}）"
            )


def build(tl: dict, cast: K.Cast, fps: int, W: int, H: int):
    timing = K.TPL["timing"]
    bg = make_bg(W, H)

    detail_cfg = (K.TPL.get("panel") or {}).get("detail")
    use_cards = bool(detail_cfg) and any(ch.get("details") for ch in tl["chapters"])
    panels: list[Image.Image] = []
    card_rows: list[list[tuple[float, Image.Image]]] | None = None
    crop_box: tuple[int, int, int, int] | None = None
    if use_cards:
        p = K.TPL["panel"]
        x0, y0, x1, y1 = (K.S(v) for v in p["box"])
        margin = K.S(int(p.get("outline_width", 2)) + 2)
        crop_box = (max(0, x0 - margin), max(0, y0 - margin),
                    min(W, x1 + margin + 1), min(H, y1 + margin + 1))
        card_rows = []
        for ch in tl["chapters"]:
            geo = detail_geometry(ch)
            rows = [(float(ch["start"]),
                     make_panel(ch, ch["index"], len(tl["chapters"]), W, H).crop(crop_box))]
            for card in ch.get("details") or []:
                _validate_card(ch, card, geo)
                rows.append((float(card["start"]),
                             make_panel(ch, ch["index"], len(tl["chapters"]), W, H,
                                        card=card).crop(crop_box)))
            for prev, cur in zip(rows, rows[1:]):
                if cur[0] <= prev[0]:
                    raise ValueError(
                        f"{ch.get('cue', '?')} / {cur[0]}: 詳細カードの時刻が増えていない"
                    )
            card_rows.append(rows)
    else:
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

    # 演技の設定は型が持つ。無ければ記号は出さず、表情だけを変える。
    acting = K.TPL.get("acting") or {}
    mark_cfg = acting.get("mark") or {}
    reaction_cfg = acting.get("reaction") or {}
    mark_lead = float(reaction_cfg.get("lead", 0.0))
    pop = float(mark_cfg.get("pop", 0.18))
    hold = float(mark_cfg.get("hold", 0.8))
    fade = float(mark_cfg.get("fade", 0.32))
    pop_amp = float(mark_cfg.get("pop_amp", 0.5))
    rise = float(mark_cfg.get("rise", 0.0))
    anchors = mark_cfg.get("anchor") or {}

    def reaction_of(cue: dict) -> dict:
        r = cue.get("react") or {}
        return r if isinstance(r, dict) else {}

    # 人物ごとの「表情が変わる時刻」。発話の頭と、聞き手の反応の頭を混ぜる。
    # 同じ時刻なら発話が勝つ（遅い方が勝つ、の同点規則）。
    face_starts: dict[str, list[float]] = {}
    face_names: dict[str, list[str]] = {}
    face_explicit: dict[str, list[bool]] = {}
    own_starts: dict[str, list[float]] = {}
    for cid in cast.order:
        events: list[tuple[float, int, str, bool]] = []
        own: list[float] = []
        for c in tl["cues"]:
            if c.get("character") == cid:
                own.append(float(c["start"]))
                events.append((float(c["start"]), 1, cast.face_for(cid, c),
                               bool(c.get("face"))))
        for c in tl["cues"]:
            entry = reaction_of(c).get(cid)
            if isinstance(entry, dict) and entry.get("face"):
                events.append((float(c["start"]), 0, str(entry["face"]), True))
        events.sort(key=lambda e: (e[0], e[1]))
        face_starts[cid] = [e[0] for e in events]
        face_names[cid] = [e[2] for e in events]
        face_explicit[cid] = [e[3] for e in events]
        own_starts[cid] = sorted(own)

    def face_at(char: str, t: float) -> tuple[str, bool]:
        """その人の最後の表情の切替を、次に変わるまで保つ。

        2 つ目は「その表情が台本に明示されていたか」。身体の揺れの倍率は、
        明示の顔にだけ掛ける（古い作品の揺れを変えないため）。
        """
        starts = face_starts.get(char) or []
        i = bisect.bisect_right(starts, t) - 1
        if i < 0:
            return cast.face_for(char, None), False
        name = face_names[char][i]
        if name not in cast.meta[char]["faces"]:
            return cast.face_for(char, None), False
        return name, face_explicit[char][i]

    # 記号の予定表。cue.start から出し、自分の次の発話が始まったら消す。
    marks: list[dict] = []
    if mark_cfg:
        for c in tl["cues"]:
            for cid, entry in reaction_of(c).items():
                if cid not in cast.chars or not isinstance(entry, dict):
                    continue
                text = str(entry.get("mark") or "")
                if not text:
                    continue
                t0 = float(c["start"]) + mark_lead
                own_next = next((s for s in own_starts.get(cid, []) if s > t0 + 1e-9),
                                math.inf)
                end = min(t0 + pop + hold + fade, own_next)
                if end <= t0:
                    continue
                marks.append({"cid": cid, "text": text, "t0": t0, "end": end})

    mark_imgs: dict[str, Image.Image] = {}
    if marks:
        fnt = K.font(int(mark_cfg.get("size", 40)), bool(mark_cfg.get("bold", True)))
        stroke = K.S(mark_cfg.get("outline_width", 3))
        fill = K.rgba(mark_cfg.get("color", [255, 209, 102, 235]))
        edge = K.rgba(mark_cfg.get("outline", [12, 20, 36, 230]))
        pad = K.S(6)
        for m in marks:
            if m["text"] in mark_imgs:
                continue
            w = int(fnt.getlength(m["text"])) + stroke * 2 + pad * 2
            asc, desc = fnt.getmetrics()
            h = asc + desc + stroke * 2 + pad * 2
            im = Image.new("RGBA", (max(1, w), max(1, h)), (0, 0, 0, 0))
            d = ImageDraw.Draw(im)
            d.text((pad + stroke, pad + stroke), m["text"], font=fnt, fill=fill,
                   stroke_width=stroke, stroke_fill=edge)
            mark_imgs[m["text"]] = im

    def smooth(x: float) -> float:
        x = max(0.0, min(1.0, x))
        return x * x * (3.0 - 2.0 * x)

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

    def draw_marks(im: Image.Image, t: float) -> None:
        for m in marks:
            if not (m["t0"] <= t < m["end"]):
                continue
            age = t - m["t0"]
            if pop > 0 and age < pop:
                u = smooth(age / pop)
                scale, alpha = 1.0 + pop_amp * (1.0 - u), u
            elif age < pop + hold:
                scale, alpha = 1.0, 1.0
            else:
                v = (age - pop - hold) / fade if fade > 0 else 1.0
                scale, alpha = 1.0, 1.0 - smooth(v)
            img = mark_imgs[m["text"]]
            if abs(scale - 1.0) > 1e-6:
                img = img.resize((max(1, int(round(img.width * scale))),
                                  max(1, int(round(img.height * scale)))),
                                 Image.LANCZOS)
            if alpha < 0.999:
                img = img.copy()
                img.putalpha(img.getchannel("A").point(lambda v: int(v * alpha)))
            slot = cast.chars[m["cid"]]["slot"]
            anchor = anchors.get(slot) or [0, 0]
            ox, oy = (K.S(v) for v in K.TPL["slots"][slot]["origin"])
            dx, dy = offset(m["cid"], t)
            ax = ox + K.S(float(anchor[0])) + dx
            ay = oy + K.S(float(anchor[1])) + dy
            if rise:
                ay -= K.S(rise * smooth(min(1.0, age / max(1e-6, pop + hold + fade))))
            im.paste(img, (ax - img.width // 2, ay - img.height // 2), img)

    def draw_frame(t: float, fi: int) -> Image.Image:
        im = bg.copy()
        ch_idx = chapter_idx_at(t)
        if ch_idx >= 0:
            slide = K.S(10) * max(0.0, 1.0 - (t - tl["chapters"][ch_idx]["start"])
                                  / timing["chapter_slide"])
            if card_rows is not None and crop_box is not None:
                rows = card_rows[ch_idx]
                starts = [row[0] for row in rows]
                ci = bisect.bisect_right(starts, t) - 1
                if ci < 0:
                    ci = 0
                p = rows[ci][1]
                if ci > 0:
                    fade_s = float(timing.get("detail_fade", 0.30))
                    gap = starts[ci] - starts[ci - 1]
                    fade_s = min(fade_s, gap)
                    age = t - starts[ci]
                    if fade_s > 0 and 0.0 <= age < fade_s:
                        p = Image.blend(rows[ci - 1][1], p, smooth(age / fade_s))
                im.paste(p, (crop_box[0], crop_box[1] + int(slide)), p)
            else:
                p = panels[ch_idx]
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
            face, explicit = face_at(cid, t)
            dx, dy = offset(cid, t)
            if explicit:
                gain = cast.gain(cid, face)
                dx, dy = int(round(dx * gain)), int(round(dy * gain))
            fig = cast.sheet(cid, face)[0 if speaker in (None, cid) else 1][lvl]
            im.paste(fig, (ox + dx, oy + dy), fig)

        draw_marks(im, t)

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
