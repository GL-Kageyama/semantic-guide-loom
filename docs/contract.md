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

⚠️ **読み違えは `line` のルビで塞ぐ。** 工房の記法 `漢字《かな》`。読みだけ仮名になり、
台詞と字幕は原表記のまま残る。

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
           "emotion": "excitement", "face": "", "chapter": 0}],
 "chapters": [{"cue": "c01", "index": 0, "label": "序章", "title": "...",
               "start": 0.4, "cue_start": 2.0, "...": "型が読む欄は素通し"}]
}
```

`wav` は**キュー単体の WAV**。口の動きはこの 1 本の包絡から作る——
`duration` の WAV から切り出すのでなく、cue ごとのファイルを測る。

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
characters/<キャスト>.cast.yaml            キャスト（配布する）
references/sheets/                        表情シート（入力。Git LFS）
projects/<作品>/                            台本（script / video / chapters / voice_fx）
projects/<作品>/assets/                     音の資材（voice / sfx / bgm）— Git LFS
projects/<作品>/renders/                    焼いた動画 — 成果物。Git LFS
build/<作品>/                               中間物（assets, audio, timeline.json）— .gitignore
```

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
