---
name: semantic-guide-loom
description: 意味のある台本から説明の映像を焼く。解説動画・社内の説明動画・研修の導入を作る。型（掛け合い・語りスライド）を選び、音の実尺から時刻を取り、Pillow で 1 コマずつ描いて ffmpeg で書き出す。AI の映像生成は使わない（同じ台本から同じ絵が出る）。
argument-hint: '(optional) 作品名か題材。例: /semantic-guide-loom works/making-a-guide / 新入社員向けの経費精算の説明 / --still 40'
---

# semantic-guide-loom — 説明の映像を焼く

「人に見せて分からせる」映像を、**台本から決定的に**組み立てる。
掛け合いでも、語りだけでもよい。**型を替えれば、同じ台本が別の絵になる。**

## 全体の流れ

```
1 素材   engine/prepare_assets.py   表情シート → 口の 3 状態（人物を置く型だけ）
2 声     semantic-audio-loom の build_voice.py   1 行 → 1 つの WAV
3 組み立て semantic-audio-loom の assemble.py     間・声量・章の印 → 1 本の WAV
4 時刻   engine/export_timeline.py  mix.yaml の実尺 → timeline.json
5 描画   engine/render.py           Pillow → ffmpeg
```

`engine/make.sh <作品>` が 5 つを順に通す。**矢印は一方向**——絵は音の実尺を読む。
音は絵を知らない。

## 作る

```bash
./engine/make.sh works/<作品名>                    # 端から端まで
./engine/make.sh works/<作品名> --still 40         # 1 枚だけ見る（数を詰めるとき）
SKIP_VOICE=1 SKIP_ASSETS=1 ./engine/make.sh <作品>  # 絵だけ焼き直す
FORCE=1 ./engine/make.sh <作品>                    # 声を作り直す
```

⚠️ **参照音声や `voice_fx.yaml` を変えたら `FORCE=1`。** 既定は既存の WAV を飛ばすので、
古い声のまま焼ける。

## 作品を書く

```
works/<作品名>/
  script.yaml     誰が・何を・どう話すか（音の台本）
  video.yaml      題・章・字幕の表記・型・キャスト（映像の台本）
  chapters.yaml   章の頭の cue（音のチャイム）
```

`video.yaml` が名乗るのは 3 つ。

```yaml
template: dialogue-bust   # templates/<name>/ の名
cast: mirai-mirabo        # casts/<name>.cast.yaml の名（人物を置かない型は書かない）
chapters:
  c07: {label: 第1章, title: 入力が、命令になる, term: 入力, key: "..."}
```

**章の中身は型が決める。** `dialogue-bust` は `term` と `key`、`narrate-slide` は
`bullets`（配列）を読む。`export_timeline.py` は素通しするだけ。

## 型

| 型 | 見た目 | 使うとき |
| --- | --- | --- |
| `dialogue-bust` | 左に人・右に相棒、中央に章の札、下に字幕 | 掛け合いで説明する |
| `narrate-slide` | 左に章の題と箇条書き、下に字幕。人物なし | 社内説明・研修 |

型は「数」（`templates/<型>/template.yaml`）と「並べ方」
（`engine/layouts/<layout>.py`）に分かれる。

- **色違い・位置違いなら YAML を 1 枚**足すだけ（`layout:` は既存のまま）
- **並べ方が違うならモジュールを 1 本**足す（`build(tl, cast, fps, W, H)` を出す）

手順と欄の一覧は `docs/template-contract.md`。

## 嵌まりどころ

- ⛔ **時刻は mix.yaml の voice stem から取る。** `pause_before` を足し直すと、
  `assemble.py` が頭尾の無音を切るぶんだけ 1 コマずつずれる。
- ⛔ **字幕は `video.yaml` の `display`。** `script.yaml` の `line` は読みのために
  カタカナで書く。そのまま出すと字幕がカタカナになる。
- **読み違えは `line` のルビで塞ぐ。** `20年《にじゅうねん》`。読みだけ仮名になり、
  台詞と字幕は原表記のまま。
- **中黒を入れすぎない。** 「オープン・エス・エス・エル」は不自然。
- **演技は「効く欄」だけで振る。** 文末の記号（`！` `？`）・`speed`・`pause_before`・
  `volume`。`emotion` は neutral かそうでないかの粗いスイッチ。`pitch`・`intonation`・
  `subtext`・`intensity` は音が動かない（semantic-audio-loom の `docs/resolve.md`）。
- **行は文の切れ目で割る。** 長い行は記号も効かない。字幕の折り返しは字数で決まるので、
  27 字を超える行は先に割る。
- **表情シートは 4列×2行の 8 マス・背景透過。** 差し替えたら `mouth_offset` を測り直す
  （`sheets/README.md`）。

## 前提

- `ffmpeg`
- venv `$HOME/sonic-loom-spike/venv_tsukasa`（Pillow・numpy・scipy・PyYAML）
- 隣に `semantic-audio-loom`（声と組み立ての正本）。`SAL=` で場所を変えられる
