# 人物 — 人物票・関係・キャスト

3 つは別のものを持つ。**混ぜない。**

| ファイル | 何 | 誰が読むか |
| --- | --- | --- |
| `characters/<id>.character.yaml` | **人物**（欲・怖れ・矛盾・感情の型） | 台本書き・`persona.py`・`export_timeline.py`（beat → face） |
| `characters/<キャスト>.persona.yaml` | **関係**（二人がどう噛み合うか） | 台本書き（人が読む） |
| `characters/<キャスト>.cast.yaml` | **画面**（誰がどこに座り、どう揺れるか） | `prepare_assets.py`・`render.py` |

## 人物票 — `characters/<id>.character.yaml`（配布する）

**一人 1 ファイル。** 作品をまたいで使い回せる人物造形。`id` は `cast.yaml` の id と
一致する。話し方だけでなく、欲・怖れ・矛盾・癖・感情の型（`emotions`）・台詞の
見本（`samples`）を持つ。**絵の欄（立ち位置・口・画像）は持たない。**

```yaml
id: mirai
name: ミライ
concept: 手で測る人。数字より、指の感触を信じる。
role: 聞き手であり、疑う人。講師にはならない。
wants: ...
fears: ...
contradiction: 任せたいのに、手を離せない。
habits: [指で机を測る, 相槌の前に一度息を止める]
humor: {what: 数字の過剰な正確さ, how: 相手の言葉を一つ借りて返す}
speech:
  register: 常体。短い。
  length: 3〜20 字
  tics: [うん, そう。, 見てな。]
  avoids: [講義口調, 感情の名指し]
emotions:                       # 感情の型。キーは自由
  pride:
    face: smile                 # cast の expressions のどれか
    voice: confidence           # SAL の 11 感情
    speed: fast
    volume: normal
    delivery: ""
    tell: 文末に「です」を足す
    body: 少し浮く
    withhold: 嬉しさを名指ししない
samples: [{beat: pride, line: "99.8%です。"}]
```

- `emotions` は 6 つ以上。`face` が cast に実在し、`voice` / `speed` / `volume` /
  `delivery` が semantic-audio-loom の語彙であることを `engine/persona.py check` が見る
- schema が必須にするのは `id` と `name` だけ。下書きを止めないため、残りは
  `check` が厳しく見る
- 形は `schemas/character.schema.json`

**顔は `beat` から決まる。** `emotions.<beat>.face` を `export_timeline.py` が解決し、
明示 `face` があればそちらを優先する（[script.md](script.md)・[acting.md](acting.md)）。

## 関係 — `characters/<キャスト>.persona.yaml`（配布する）

`cast.yaml` が**画面の誰か**、`character.yaml` が**人物**、`persona.yaml` が
**関係**。人物の欄は持たない（旧形式の `characters[]` は読み込みの後方互換）。

```yaml
name: mirai-mirabo
description: 人と小さな機体。疑い、確かめ、最後に少しだけ任せる。
pair:
  engine: ミライが問いを立て、ミラボが予測で応え、ミライが具体で崩す。
  rule: ミラボの数字は、ミライの具体に回収される。
  dynamics:
    - between: [mirai, mirabo]
      engine: 予測 → 具体 → 予測の外れ。
      rule: ミラボは当てにいき、ミライは当てさせない。
      escalation: ミラボが数字を増やし、ミライが黙る。
```

- `engine/persona.py check` が cast の id と人物票の対応、`dynamics` の id、
  `emotions` の語彙を見る
- `engine/persona.py brief` が台本を書く前の人物票（感情表・samples 込み）を出す。
  `--character <id>` で一人ぶん
- `engine/persona.py analyze --project` が既存台本から話し方の実測を出す
- 形は `schemas/persona.schema.json`

## キャスト — `characters/<キャスト>.cast.yaml`（配布する）

キャストは「誰が画面に居るか」。**立ち位置は型が持ち、キャストは `slot` の名で座る。**
役者はデータで、コードに名前を書かない。

```yaml
name: mirai-mirabo
default_expression: neutral
mouth_states: [["m0", 1.0], ["m1", 0.42]]   # 開・半開の深さの比

characters:
  - id: mirai                 # script.yaml の character と一致させる
    name: ミライ
    slot: left                # template.yaml の slots の鍵
    sheet: ミライ_表情差分シート.png   # references/sheets/ の下
    canvas: [420, 480]        # 切り出しの画布
    scale: 1.15               # 型の枠に合わせる拡大率
    expressions: [neutral, smile, ...]     # シートの 8 マス（左上から右へ）
    blink: {neutral: blink_neutral, ...}   # 表情 → 閉じ目（データのみ。描画は使わない）
    by_emotion: {joy: smile, ...}          # 明示の face が無いコマの既定
    lip: true                 # 口パクをするか
    mouth_offset: [4.0, 66.0] # 目の中心 → 口の中心（画布の座標）
    mouth: {box: [26, 14, 8], drop: 7.5, inner: [118, 66, 70]}
    motion:                   # sin 波の重ね合わせ
      - {axis: y, amp: 1.5, hz: 1.1}
    motion_gain:              # 表情 → 身体の揺れの倍率（任意）
      surprised: 1.3
      worried: 0.7
```

- **シートは 4 列×2 行 = 8 マス**。並びは `expressions` が決める。
- `lip: false` の側は口を動かさない（3 状態とも同じ絵が返る）。
- `motion` の `amp` は 720p 基準の画素。`axis` は `x` か `y`。
- **`mouth_offset` はシートごとに測り直す値**。目の中心から口の中心までのずれ。
- `by_emotion` は**後方互換の既定**。新しい作品は `beat` から顔が決まる
  （明示 `face` があれば優先）。
- `motion_gain` は解決済みの `face` に掛かる（未記載 1.0）。
- **まばたきはしない。** `blink` は旧データを読めるように残しているだけで、
  描画も演技の skill も使わない。
- 形は `schemas/cast.schema.json`

## 表情シート

`references/sheets/` に置く（入力。Git LFS）。**4 列×2 行の 8 マス**で、左上から
右へ `expressions` の順に並ぶ。`prepare_assets.py` がマスを切り出し、口の 3 状態を
作り、`build/<作品>/assets/faces.json` に錨を書く（[usage.md](usage.md) の 1 段）。

**シートは作品ではなく資材。** 同じ人物を別の作品でも使うなら、同じシートを指す。
切り抜きから元のシートへは戻せないので、LFS で入れる（[placement.md](placement.md)）。
