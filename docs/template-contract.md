# 型とキャスト — 絵の側の契約

**型は絵の側だけを持つ。意味は持たない。** 同じ台本を別の型で焼けることが、
このリポジトリの目的そのもの。

型は 2 つの部品からなる。

| 部品 | 置き場 | 何を持つか |
| --- | --- | --- |
| 数 | `templates/<型>/template.yaml` | 画布・色・書体・位置・間合い |
| 並べ方 | `engine/layouts/<layout>.py` | その数を使って 1 コマを描く関数 |

`template.yaml` の `layout:` が、どの `layouts/*.py` を呼ぶかを名乗る。
**数だけの型**（掛け合いの色違い・位置違い）は YAML を 1 枚足すだけで済む。
**並べ方が違う型**（スライド・図解）は、`layouts/` にモジュールを 1 本足す。

---

## `template.yaml` の欄

座標と長さはすべて **720p 基準**。1080p で焼くと `render.py` が `H / 720` 倍する。
型が `canvas.height` に 1080 と書いても、**数字の基準は 720 のまま**（画布の大きさだけが変わる）。

### どの型も持つ欄

```yaml
name: dialogue-bust
description: 一行で何の型か
layout: dialogue_bust        # engine/layouts/<これ>.py

canvas: {width: 1280, height: 720}

font:
  path: "/System/Library/.../BIZ_UDGothic.ttc"
  regular: 0                 # ttc の面
  bold: 1

palette:                     # 名前 → [r,g,b] か [r,g,b,a]。layouts は名前で引く
  ink: [...]
  accent: [...]
  ...

background:                  # 型ごとに形が違ってよい（下記）
  ...

progress:                    # 最下部の帯。どの型も同じ意味を持つ
  bar_height: 6
  tick_height: 10
  tick_width: 2
  tick_color: [r,g,b,a]
  track_color: [r,g,b,a]

timing:
  subtitle_lead: 0.05        # 発話の何秒前から字幕を出すか
  subtitle_tail: 0.45        # 発話の何秒後まで残すか
  speaker_tail: 0.25         # 話し手の強調を何秒残すか
  chapter_slide: 0.45        # 札が滑り込む時間
  chapter_lead: 1.6          # 札を cue の何秒前から出すか（export_timeline が読む）
```

### `dialogue-bust` が持つ欄

`slots`（立ち位置）、`dim_when_silent`、`mouth`（声 → 口の 3 状態の閾値）、
`panel`（章の札）、`subtitle`、`header`。
全欄は `templates/dialogue-bust/template.yaml` を見る。

### `narrate-slide` が持つ欄

`accent_band`（左端の帯）、`slide`（章の題と箇条書き）、`subtitle`、`header`。
人物を置かないので `slots` も `mouth` も持たない。

---

## `layouts/<layout>.py` の契約

モジュールは関数を 1 つ出す。

```python
def build(tl: dict, cast, fps: int, W: int, H: int):
    ...
    return draw_frame          # (t: float, fi: int) -> PIL.Image
```

- `tl` … `timeline.json` をそのまま
- `cast` … `common.Cast`。型が人物を置かないときは `None`
- 寸法・色・書体は `common.S(v)` / `common.C("名前")` / `common.font(size, bold)` で引く
- 進捗の帯は `common.progress_bar(im, t, tl, W, H)` を呼ぶ（型が持つ数字を使う）

**1 コマは状態を持たない。** `draw_frame(t, fi)` は時刻だけから絵を決める。
ゆえに途中から焼いても、同じ時刻なら同じ絵が出る（`--start` / `--still`）。

---

## `cast.yaml` の欄

キャストは「誰が画面に居るか」。立ち位置は型が持ち、キャストは `slot` の名で座る。

```yaml
name: mirai-mirabo
default_expression: neutral
mouth_states: [["m0", 1.0], ["m1", 0.42]]   # 開・半開の深さの比

characters:
  - id: mirai                 # script.yaml の character と一致させる
    name: ミライ
    slot: left                # template.yaml の slots の鍵
    sheet: ミライ_表情差分シート.png   # sheets/ の下
    canvas: [420, 480]        # 切り出しの画布
    scale: 1.15               # 型の枠に合わせる拡大率
    expressions: [neutral, smile, ...]     # シートの 8 マス（左上から右へ）
    blink: {neutral: blink_neutral, ...}   # 表情 → 閉じ目の表情（使う型のみ）
    by_emotion: {joy: smile, ...}          # script の emotion → 表情
    lip: true                 # 口パクをするか
    mouth_offset: [4.0, 66.0] # 目の中心 → 口の中心（画布の座標）
    mouth: {box: [26, 14, 8], drop: 7.5, inner: [118, 66, 70]}
    motion:                   # sin 波の重ね合わせ
      - {axis: y, amp: 1.5, hz: 1.1}
```

- **シートは 4列×2行 = 8 マス**。並びは `expressions` が決める。
- `lip: false` の側は口を動かさない（3 状態とも同じ絵が返る）。
- `motion` の `amp` は 720p 基準の画素。`axis` は `x` か `y`。
- **`mouth_offset` はシートごとに測り直す値**。目の中心から口の中心までのずれ。

---

## 型を足す手順

1. `templates/<新しい型>/template.yaml` を作る。既存の型を写して色と数を変える。
2. 並べ方が同じなら、**それだけで終わり**（`layout:` は既存のまま）。
3. 並べ方が違うなら `engine/layouts/<新しい型>.py` を書き、`layout:` で名乗る。
   - 文字は `common.wrap_jp` / `common.wrap_balanced` / `common.text_img` を使う
   - 背景と札は自前で描く（型ごとに違ってよい）
4. `./engine/make.sh <作品>` で焼き、`--still` で 1 枚見て、数を詰める。

**型は作品を知らない。** 特定の題・特定の人数・特定の章の数を、型に書かない。
