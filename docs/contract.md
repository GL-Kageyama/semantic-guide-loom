# 契約 — どのファイルが、何を持ち、誰が読むか

5 つの段は、**4 つのファイルで継がっている**。段をまたぐ受け渡しは、
この 4 つにしかない。

```
script.yaml ──(build_voice)──> voice/*.wav ──(assemble)──> mix.yaml + renders/<name>.wav
     │                                                          │
     │                                                    (export_timeline)
     │                                                          ↓
     └───────────────────────────────────────────> timeline.json
                                                                 │
video.yaml ──(template / cast の名)───────────────────────────────┤
                                                                 ↓
                                          (render) ──> projects/<作品>/renders/<name>.mp4
```

この 4 つに**任意の 4 つ**が重なる。どれも無ければ、従来の 5 段のまま動く。

```
reading.yaml ──(reading.py stage)──> build/<作品>/script.yaml + video.yaml
                                          ↑ line を読みに、display に原表記
bgm.yaml ──(bgm.py generate / mix)──> assets/bgm/<name>.wav + mix.yaml の bed と duck
characters/<id>.character.yaml ──(人は check / brief。engine は beat→face の解決にも読む)──> 台本と演技
characters/<キャスト>.persona.yaml ──(関係。人が読む)──> 掛け合いの型
```

**向きが一方通行であることが、この機構の要**。絵は音の実尺を読む。音は絵を知らない。
ゆえに台本を書き換えても、絵の側の時刻を手で直す必要はない。

---

## `script.yaml` — 音の台本（作品が持つ）

semantic-audio-loom の scene 形式。`semantic-audio-loom/projects/longform/` の作品と
**同じもの**。1 cue = 1 行 = 1 つの声のファイル。**形の正本は
`semantic-audio-loom/schemas/scene.schema.json`**（このリポジトリに写しを置かない）。

```yaml
name: cyber-basics
default_pause: 0.25           # cue と cue のあいだの既定の間（秒）
cues:
  - {character: mirai, line: "入力、メモリ、依存。", speed: fast,
     pause_before: 0.35, name: c04}
```

- `character` … semantic-audio-loom の `characters/<id>.voice.yaml` の id
- `line` … **Tsukasa が読む形**。字幕とは別（下記 `display`）
- `name` … cue の id。`mix.yaml` と `timeline.json` はこの名で継ぐ
- 演技の欄（`emotion` / `speed` / `pause_before` / `volume` / `pitch` …）は
  semantic-audio-loom の仕様。**効く欄は限られる**（semantic-audio-loom の
  `docs/resolve.md`「どの欄が、声を動かすか」を見る）

### 演技の欄 — 声と絵の両方へ渡る

```yaml
- name: c009
  character: mirabo
  line: "99.8パーセント。"
  emotion: confidence       # 声（SAL の 11 感情）
  beat: pride               # 演技の正本。人物票の感情キー
  face: smile               # 省略可（明示があれば beat より優先）
  speed: fast
  pause_before: 0.3
  volume: normal
  react:                    # 聞き手の反応（この cue の間）
    mirai: {beat: doubt, mark: "？"}
```

- **`beat` が演技の正本。** `face` は省略してよく、人物票の
  `emotions.<beat>.face` から解決される。明示 `face` があればそちらを優先し、
  どちらも無ければ `cast.yaml` の `by_emotion[emotion]` に落ちる。
- `react` の id は cast の id。`face` / `beat` は cue と同じ規則で解決され、
  `mark` は 3 文字まで。**顔だけ・記号だけでもよい**が、どちらも無い反応は無効。
- **解決するのは `export_timeline.py` の 1 か所だけ**（規則は
  `engine/characters.py`）。`timeline.json` には解決済みの `face` と
  `react.<id>.face` が入り、`beat` も記録として残る。絵を描く側は推測しない。

⚠️ **読み違えは `line` のルビで塞ぐ。** 工房の記法 `漢字《かな》`。読みだけ仮名になり、
台詞と字幕は原表記のまま残る。ただし**読みを本気で直すなら `reading.yaml`**（下記）。
両方を同じ作品に混ぜない。ルビは `reading.yaml` の無い作品のための後方互換。

---

## `reading.yaml` — 読み（作品が持つ。任意）

声に読ませる文だけを持つ。**字幕・章題・`timeline.json` の `text` には渡さない。**

```yaml
name: black-swan-ai
readings:
  c001: "みらいさん。『ぶらっくすわん』って、くろいはくちょうのこと、ですよね？"
  c250: "にせんにじゅうにねんじゅういちがつみっか"
needs_review: [c007, c250]      # 数字・%・Latin を残した cue（人が決める）
```

- `readings` … cue の名 → 声に読ませる文（かな。外来語はカタカナ可）
- 句読点・`……`・`？`・`！` は残す（間と抑揚がそこから作られる）
- `engine/reading.py draft` が下書きし、`audit` が残存漢字・数字・`%`・Latin を見る
- 形は `schemas/reading.schema.json`

### 読みの舞台 — `build/<作品>/`

`make.sh` は `reading.yaml` があるときだけ、2 の前に `reading.py stage` を呼ぶ。

```
projects/<作品>/script.yaml ─┐
projects/<作品>/video.yaml  ─┤ stage
projects/<作品>/reading.yaml ┘
        ↓
build/<作品>/script.yaml   line = readings[cue]
build/<作品>/video.yaml    display[cue] = 元の display か line（原表記）
build/<作品>/chapters.yaml / voice_fx.yaml / sfx.yaml / bed_mute.yaml
```

**作品のファイルは書き換えない。** 声は舞台の `line` から、字幕は舞台の `display` から
出る。`export_timeline.py` の `name` と `render.py` の資材の道が揃うよう、舞台は
`build/<作品名>/` に作る（`<作品名>` は作品ディレクトリの basename）。

`--prune-voice` は `assets/voice/<cue>.params.yaml` の `reading` か `dialogue` が
新しい読みと違う cue の WAV だけを消す。`make.sh` は声を作る回だけ付ける。

---

## `bgm.yaml` — 敷き音の意図（作品が持つ。任意）

話から決めた意図と、ミックスの値を持つ。**音そのものは `assets/bgm/<name>.wav`。**

```yaml
name: underlay
prompt: "A continuous soft ambient pad, warm evolving chords, ... no drums, no vocals"
mood: [calm, curious, unease]
duration: 90            # assemble が全体長へ継ぎ足すので 90 秒で足りる
segment_s: 30           # MusicGen の上限
seeds: auto             # prompt の SHA1 から決定的に。または整数の配列
crossfade_s: 2.5
level_gain_db: 8.0
level_limit: 0.95
provider_settings: {tokens: 1500, guidance_scale: 3.0}
mix:
  gain_db: -8.0
  duck: {threshold_db: -30, depth_db: 3.0, attack_s: 0.03, release_s: 0.45}
```

- `engine/bgm.py generate` は `assets/bgm/<name>.params.yaml` の `input_sha1` を見て、
  入力が変わったときだけ作り直す。`--force` / `BGM=force` は常に作り直す
- `engine/bgm.py mix` は `assemble.py` が書いた `mix.yaml` の bed `gain_db` と
  `duck` を `mix.gain_db` / `mix.duck` へ直し、SAL の `bin/mix.py` で混ぜる
- **`mix.yaml` を手で直さない。** 直しても次の `make.sh` で戻る。正本は `bgm.yaml`
- 形は `schemas/bgm.schema.json`

---

## `characters/<id>.character.yaml` — 人物票（配布する）

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

## `characters/<キャスト>.persona.yaml` — 二人の関係（配布する）

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

---

## `design.md` — 設計（作品が持つ。任意）

台本を書く前の設計。題材・視聴者・約束・事実の柱・**説明の鎖**・章・二人の役割・
最後に残す問い。**形は決めない**（Markdown）。`guide-design` の
`references/design-sheet.md` が型。

**説明の鎖**は、視聴者が台本だけで復元できる問い（3〜7 個）と、それを平文で言う
場所の対応。**主題（約束）はここに入れない。** 主題は言わない。事実と因果は言う。
この表が `review/viewers/<版>/facts.yaml` の元になる。

---

## `review/` — 二つの台帳（混ぜない）

台本の採否は、**別々の物差し**を両方通す。平均も足さない。

| 台帳 | 何を見るか | 道具 | 合格 |
| --- | --- | --- | --- |
| `review/reports/<版>/` | 文学評議会の 10 次元（物語・人物・情感） | `engine/review.py` | 平均 60 超 |
| `review/viewers/<版>/` | 初見の復元テスト（3 人）と説明の評価（1 人） | `engine/viewer.py` | 理解度は平文の基準 − 10 以上、各事実が 2/3 以上、説明 75 以上 |

```
review/viewers/<版>/
  facts.yaml       視聴者が答えるべき問い（id / question / answer）
  r1.json r2.json r3.json   初見の読者の返答（schemas/viewer.schema.json）
  explanation.json 説明の設計の評価
review/viewers/<版>.yaml   集計と門の判定（engine/viewer.py record が書く）
review/viewers/<基準>/plain.md   同じ事実を平文で書いた基準版
review/viewers/<基準>.yaml       基準の理解度（engine/viewer.py baseline が書く）
```

- **文学評議会は、説明の明瞭さを測らない。** 10 次元は物語としての強さを見る。
  断片・省略・余白が高得点になりうるので、解説動画には別の門が要る。
- **理解度の絶対値 75 は、平文の解説のための数字。** 掛け合いと感情の層を持つ
  台本は、同じ事実でも自己申告の理解度が下がる。同じ事実を平文で書いた基準版を
  同じ 3 人に読ませ、**基準の平均 − 10 点**を掛け合い版のしきい値にする。
  基準は台本より先に、`facts.yaml` と `design.md` から書く。事実の復元（2/3）と
  説明の評価（75）は基準でも変えない。
- **`review/reports/` に視聴者の JSON を置かない。** `review.py` が全部評価者として
  数え、文学の平均が壊れる。置き場を分ける。
- 読者には台本だけを渡す。`design.md`・人物票・前の評価を見せない。

---

## `video.yaml` — 映像の台本（作品が持つ）

音には渡さない。`export_timeline.py` が読み、`timeline.json` に写す。

```yaml
title: 脆弱性とサイバー攻撃
subtitle: なぜ、同じ三つなのか
channel: MIRAI × MIRABO
template: dialogue-bust        # references/templates/<name>/ の名
cast: mirai-mirabo             # characters/<name>.cast.yaml の名。人物を置かない型は書かない
width: 1280                    # 省略時 1280
height: 720                    # 省略時 720
fps: 30                        # 省略時 30
chapters:                      # cue の名 → 章
  c07: {label: 第1章, title: 入力が、命令になる, term: 入力,
        key: "信じた文字列が、\n実行される。"}
display:                       # cue の名 → 字幕の文（原表記）
  c05: "20年も？"
```

- **`chapters` の中身は型が決める。** `export_timeline` は素通しするだけ。
  `dialogue-bust` は `term` と `key` を読み、`narrate-slide` は `bullets`（配列）を読む。
- **`display` は「音の表記」と「字幕の表記」を割るための欄。** `line` はカタカナで
  読ませ、字幕は原表記で出す、という使い方をする。無い cue は `line` がそのまま出る。

## `chapters.yaml` — 章の頭（音が持つ）

```yaml
- c01
- c07
```

cue の名の配列。`assemble.py` がこの cue の手前にチャイムを置く。
**`video.yaml` の `chapters` とは別物**——あちらは絵の札、こちらは音の合図。

## `mix.yaml` — 組み立ての結果（派生。手で編集しない）

`assemble.py` が `script.yaml` と `voice/` の実尺から書く。
`timeline.json` の時刻は、**このファイルの voice stem の `start` と WAV の長さ**から取る。

`bgm.yaml` がある作品では、`bgm.py mix` が bed の `gain_db` と `duck` を
`bgm.yaml` の `mix` で上書きする。**それも含めて `mix.yaml` は派生**で、手で編集しない。

⚠️ **`pause_before` を足し直して時刻を作らない。** `assemble.py` は各キュー頭尾の
無音を切るので、足し直すと 1 コマずつずれる。

## `timeline.json` — 音と絵の唯一の継ぎ目（派生）

`export_timeline.py` が書き、`render.py` だけが読む。

```json
{
 "name": "...", "project": "/abs/path/projects/cyber-basics",
 "title": "...", "channel": "...",
 "template": "dialogue-bust", "cast": "mirai-mirabo",
 "fps": 30, "width": 1280, "height": 720, "duration": 287.27,
 "audio": "/abs/path/renders/cyber-basics.wav",
 "cues": [{"name": "c01", "character": "mirabo", "start": 2.0, "end": 3.1,
           "wav": "/abs/path/c01.wav", "text": "ミライさん！",
           "emotion": "excitement", "face": "excited", "beat": "pride",
           "react": {"mirai": {"face": "thinking", "beat": "doubt", "mark": "？"}},
           "chapter": 0}],
 "chapters": [{"cue": "c01", "index": 0, "label": "序章", "title": "...",
               "start": 0.4, "cue_start": 2.0, "...": "型が読む欄は素通し"}]
}
```

`wav` は**キュー単体の WAV**。口の動きはこの 1 本の包絡から作る——
`duration` の WAV から切り出すのでなく、cue ごとのファイルを測る。

`face` / `react` は**解決済み**の値が入る（明示 `face` → `beat` → `emotion` の
対応表 → 既定）。`beat` もそのまま残るが、絵は読まない（監査と記録のため）。

`project` は作品の置き場。`render.py` が、書き出し先を決め損ねたときの既定
（`<project>/renders/<name>.mp4`）に使う。

---

## `references/templates/<name>/template.yaml` — 型（絵の側）

型が持つのは**絵の側だけ**。色・書体・位置・間合い。意味は持たない。
欄の一覧と意味は `docs/template-contract.md`、形は `schemas/template.schema.json`。

## `characters/<name>.cast.yaml` — キャスト（誰が画面に居るか）

役者は**データ**。コードに名前を書かない。欄は `docs/template-contract.md`、
形は `schemas/cast.schema.json`。

## `faces.json` — 切り出した素材（派生）

`prepare_assets.py` が `build/<作品名>/assets/` に書く。`render.py` と `Cast` が読む。
シートから測った口の錨（`pt`）と、表情 → 画像ファイルの対応表が入る。

---

## 置き場

```
references/templates/<型>/template.yaml   型（配布する）
characters/<キャスト>.cast.yaml            キャスト・画面（配布する）
characters/<id>.character.yaml             人物票・一人 1 ファイル（配布する）
characters/<キャスト>.persona.yaml         キャストの関係（配布する）
references/sheets/                        表情シート（入力。Git LFS）
projects/<作品>/                            台本（script / video / chapters / voice_fx /
                                          design / reading / bgm / review）
projects/<作品>/review/acting/             感情の弧（plan.md）と版ごとの計測（vN.yaml）
projects/<作品>/review/viewers/            初見復元テストと説明の評価（vN/ と vN.yaml）
projects/<作品>/assets/                     音の資材（voice / sfx / bgm）— Git LFS
projects/<作品>/renders/                    焼いた動画 — 成果物。Git LFS
build/<作品>/                               中間物（assets, audio, 読みの舞台, timeline.json）
                                          — .gitignore
```

**演技の計測は `review/acting/` に置く。** `review/reports/` は評価者の JSON だけの
場所で、`review.py` はそこの全 `*.json` を評価者として数える。YAML の計測を
混ぜると平均が壊れる。

**入れるのは「入力」と「成果物」、入れないのは「中間物」。** 表情シートも声も入力
（切り抜きからも、声からも元には戻せない）、`renders/` は成果物（clone した人がそのまま
見られる）。`build/` は焼き直せば戻るので入れない。

`projects/<作品>/assets/` の中でも、`voice_trim/` `voice_fx/` `renders/` `*_tiled.wav`
`*_short.wav` は `assemble.py` が作る派生なので `.gitignore`。**入るのは `voice/*.wav`
と、効果音・敷き音の原盤だけ。** ⚠️ **`assets/renders/`（組み立てた WAV）と
作品の `renders/`（焼いた MP4）は別物**——前者は中間物、後者は成果物。

**作品はこのリポジトリに無くてもよい。** `make.sh` は `script.yaml` と `video.yaml` の
あるディレクトリならどこでも指せる。その場合、音の資材は `projects/<作品>/assets/` が
無ければ `build/<作品>/audio` に作られ、動画は作品の `renders/` へ出る。
