# 型 — 絵の側の契約

**型は絵の側だけを持つ。意味は持たない。** 同じ台本を別の型で焼けることが、
このリポジトリの目的そのもの。

型は 2 つの部品からなる。

| 部品 | 置き場 | 何を持つか |
| --- | --- | --- |
| 数 | `references/templates/<型>/template.yaml` | 画布・色・書体・位置・間合い |
| 並べ方 | `engine/layouts/<layout>.py` | その数を使って 1 コマを描く関数 |

`template.yaml` の `layout:` が、どの `layouts/*.py` を呼ぶかを名乗る。
**数だけの型**（掛け合いの色違い・位置違い）は YAML を 1 枚足すだけで済む。
**並べ方が違う型**（スライド・図解）は、`layouts/` にモジュールを 1 本足す。

**型は作品を知らない。** 特定の題・特定の人数・特定の章の数を、型に書かない。

## いまある型

| 型 | 見た目 | 使うとき |
| --- | --- | --- |
| `dialogue-bust` | 左に人・右に相棒、中央に章の札、下に字幕。章の中で詳細カードが切り替わる | 掛け合いで説明する。4〜5 分に耐える |
| `narrate-slide` | 左に章の題と箇条書き、下に字幕。人物なし | 社内説明・研修。1 章 = 1 枚で読み物として立つ |

## `template.yaml` の欄

座標と長さはすべて **720p 基準**。1080p で焼くと `render.py` が `H / 720` 倍する。
型が `canvas.height` に 1080 と書いても、**数字の基準は 720 のまま**（画布の大きさだけが
変わる）。

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

background:                  # 型ごとに形が違ってよい
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
`panel`（章の札と詳細カード）、`subtitle`、`header`、`acting`（聞き手の反応と記号）。
全欄は `references/templates/dialogue-bust/template.yaml` を見る。

`acting` の形と描画の規則は [acting.md](acting.md)。

### 詳細カード — `panel.detail`（`dialogue-bust`）

`video.yaml` の `chapters[].details` を、章のヘッダ（label / term / title / key）の
下で切り替える。**ヘッダは動かない。** `details` が無い章・作品は、今までどおり
`key` 1 枚を章の間ずっと貼る（`panel.detail` の無い古い型も同じ）。

```yaml
panel:
  detail:
    head: {size: 22, bold: true}   # 見出し。色は layout が warm
    head_gap: 6
    line: {size: 22, step: 27}     # 本文。色は layout が ink
    max_lines: 4                   # 章題が 1 行のときの上限

timing:                            # 同じ template.yaml の別の節
  detail_fade: 0.30                # カードの切替のクロスフェード（0 で即時）
```

- **容量は章題の行数から決まる。** 本文の開始はヘッダが描き終わる y、下端は箱の
  下端 − pad。1 行章題なら **4 行**、2 行章題なら **3 行**（720p）。`max_lines` は
  上限で、実容量を超える指定は実容量で切られる。`scriptcheck.py` が同じ計算で弾く。
- **切り替えは `details[].start`（`timeline.json`）で決まる。** 1 コマは状態を
  持たず、`bisect` でその時刻のカードを選ぶ。切替の `detail_fade` 秒だけ前後の
  カードを `Image.blend` する。**章の切替では blend しない**（従来の slide だけ）。
- 詳細を持つ作品だけ、パネルを**箱＋輪郭の数 px に切り詰めて**持つ（外は完全透明。
  貼る結果はフルキャンバスと同じ）。詳細が無ければ従来の 1 枚経路のまま。
- `head` が 1 行に収まらない・行が容量を超える・色名が無い、は**黙って切らずに
  失敗**する（章 cue と詳細 cue を名指しする）。

### `narrate-slide` が持つ欄

`accent_band`（左端の帯）、`slide`（章の題と箇条書き）、`subtitle`、`header`。
人物を置かないので `slots` も `mouth` も持たない。

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

## 型を足す手順

1. `references/templates/<新しい型>/template.yaml` を作る。既存の型を写して色と数を変える。
2. 並べ方が同じなら、**それだけで終わり**（`layout:` は既存のまま）。
3. 並べ方が違うなら `engine/layouts/<新しい型>.py` を書き、`layout:` で名乗る。
   - 文字は `common.wrap_jp` / `common.wrap_balanced` / `common.text_img` を使う
   - 背景と札は自前で描く（型ごとに違ってよい）
4. `./engine/make.sh projects/<作品>` で焼き、`--still` で 1 枚見て、数を詰める。

形は `schemas/template.schema.json`。キャストの欄は [characters.md](characters.md)。
