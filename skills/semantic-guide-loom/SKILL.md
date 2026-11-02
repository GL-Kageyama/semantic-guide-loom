---
name: semantic-guide-loom
description: 意味のある台本から説明の映像を焼く。解説動画・社内の説明動画・研修の導入を作る。型（掛け合い・語りスライド）を選び、音の実尺から時刻を取り、Pillow で 1 コマずつ描いて ffmpeg で書き出す。AI の映像生成は使わない（同じ台本から同じ絵が出る）。日本語のみ（多言語化はしない）。
argument-hint: '(optional) 作品名か題材。例: /semantic-guide-loom projects/making-a-guide / 新入社員向けの経費精算の説明 / --still 40'
---

# semantic-guide-loom — 説明の映像を焼く

「人に見せて分からせる」映像を、**台本から決定的に**組み立てる。
掛け合いでも、語りだけでもよい。**型を替えれば、同じ台本が別の絵になる。**

## 全体の流れ

台本がまだ無いなら、**設計から始める**。スキルが 5 つ、焼くのが `engine/make.sh`。

```
設計  guide-design    題材 → design.md（約束・章・事実の柱）
人物  guide-cast      design.md + 既存台本 → characters/<キャスト>.persona.yaml
台本  guide-script    design.md + persona → 生成 → 評議会（平均 60 超）→ 採用版
読み  guide-reading   script.yaml + reading.yaml → 監査 → ビルド用の舞台
BGM   guide-bgm       台本・章 → bgm.yaml → MusicGen → underlay.wav
焼く  semantic-guide-loom
```

```
1 素材   engine/prepare_assets.py   表情シート → 口の 3 状態（人物を置く型だけ）
2 声     semantic-audio-loom の build_voice.py   1 行 → 1 つの WAV
3 組み立て semantic-audio-loom の assemble.py     間・声量・章の印 → 1 本の WAV
4 時刻   engine/export_timeline.py  mix.yaml の実尺 → timeline.json
5 描画   engine/render.py           Pillow → ffmpeg
```

`engine/make.sh <作品>` が 5 つを順に通す。**矢印は一方向**——絵は音の実尺を読む。
音は絵を知らない。

`reading.yaml` があれば、2 の前に `engine/reading.py stage` が
`build/<作品>/` に舞台を作る（`line` を読みに差し替え、`display` に原表記を補う）。
`bgm.yaml` があれば、3 で `engine/bgm.py` が生成とミックスを行う。
**どちらも無ければ、今までどおりの 5 段**。

## 台本を、設計から作る

| 段 | スキル | 作るもの | 道具 |
| --- | --- | --- | --- |
| 設計 | `guide-design` | `projects/<作品>/design.md` | story-council（plot モード） |
| 人物 | `guide-cast` | `characters/<キャスト>.persona.yaml` | `engine/persona.py` |
| 台本 | `guide-script` | `台本.md` → `script.yaml` / `video.yaml` / `chapters.yaml` | story-council（8 次元）・`engine/review.py`・`engine/scriptcheck.py` |
| 読み | `guide-reading` | `reading.yaml`（声に読ませるかな） | `engine/reading.py` |
| BGM | `guide-bgm` | `bgm.yaml` → `assets/bgm/underlay.wav` | `engine/bgm.py` |

プラグインとして入っているときは、呼び名に接頭辞が付く
（`/semantic-guide-loom:guide-design`）。

- **採用は平均 60 超の最高版。** `engine/review.py table --project <作品>` で推移を見る。
- **キャストは画面、ペルソナは言葉。** `cast.yaml` は絵の側だけ、`persona.yaml` は話し方。
- **読みは音のためだけ。** 字幕・章題には渡さない。`display` が原表記を持つ。
- **BGM は話から毎回作る。** `mix` の利得と ducking も `bgm.yaml` が持つ
  （`assemble.py` の −30/14 を上書きする）。

## 作る

```bash
./engine/make.sh projects/<作品名>                    # 端から端まで
./engine/make.sh projects/<作品名> --still 40         # 1 枚だけ見る（数を詰めるとき）
SKIP_VOICE=1 SKIP_ASSETS=1 ./engine/make.sh <作品>    # 絵だけ焼き直す
FORCE=1 ./engine/make.sh <作品>                       # 声を作り直す
BGM=force ./engine/make.sh <作品>                     # 敷き音も作り直す
BGM=0 ./engine/make.sh <作品>                         # 敷き音の段を飛ばす
```

焼いた動画は**作品の隣**に出る（`projects/<作品名>/renders/<作品名>.mp4`）。

⚠️ **参照音声や `voice_fx.yaml` を変えたら `FORCE=1`。** 既定は既存の WAV を飛ばすので、
古い声のまま焼ける。

## 作品を書く

```
projects/<作品名>/
  design.md       題材・約束・章・事実の柱（任意。設計から作るとき）
  reading.yaml    cue → 声に読ませる読み（任意。無ければ line をそのまま読む）
  bgm.yaml        敷き音の意図とミックス（任意。無ければ BGM の段を飛ばす）
  script.yaml     誰が・何を・どう話すか（音の台本）
  video.yaml      題・章・字幕の表記・型・キャスト（映像の台本）
  chapters.yaml   章の頭の cue（音のチャイム）
  assets/voice/   1 行 1 つの声（+ .params.yaml）
  assets/sfx/  assets/bgm/   効果音・敷き音
```

`video.yaml` が名乗るのは 3 つ。

```yaml
template: dialogue-bust   # references/templates/<name>/ の名
cast: mirai-mirabo        # characters/<name>.cast.yaml の名（人物を置かない型は書かない）
chapters:
  c07: {label: 第1章, title: 入力が、命令になる, term: 入力, key: "..."}
```

**章の中身は型が決める。** `dialogue-bust` は `term` と `key`、`narrate-slide` は
`bullets`（配列）を読む。`export_timeline.py` は素通しするだけ。

形は `schemas/`（`video` / `template` / `cast` / `persona` / `reading` / `bgm`）。
`script.yaml` の形の正本は `semantic-audio-loom/schemas/scene.schema.json`。

## 型

| 型 | 見た目 | 使うとき |
| --- | --- | --- |
| `dialogue-bust` | 左に人・右に相棒、中央に章の札、下に字幕 | 掛け合いで説明する |
| `narrate-slide` | 左に章の題と箇条書き、下に字幕。人物なし | 社内説明・研修 |

型は「数」（`references/templates/<型>/template.yaml`）と「並べ方」
（`engine/layouts/<layout>.py`）に分かれる。

- **色違い・位置違いなら YAML を 1 枚**足すだけ（`layout:` は既存のまま）
- **並べ方が違うならモジュールを 1 本**足す（`build(tl, cast, fps, W, H)` を出す）

手順と欄の一覧は `docs/template-contract.md`。

## 嵌まりどころ

- ⛔ **時刻は mix.yaml の voice stem から取る。** `pause_before` を足し直すと、
  `assemble.py` が頭尾の無音を切るぶんだけ 1 コマずつずれる。
- ⛔ **字幕は `video.yaml` の `display`。** `script.yaml` の `line` は読みのために
  カタカナで書く。そのまま出すと字幕がカタカナになる。
- **読み違えは `reading.yaml` で塞ぐ。** cue ごとに、声に読ませるかなを書く。
  字幕は `display` が原表記を持ち続ける（`/guide-reading`）。
  ルビ（`20年《にじゅうねん》`）は `reading.yaml` が無い作品のための後方互換。
- **BGM の音量は `bgm.yaml` が持つ。** `mix.yaml` を手で直しても、次の
  `make.sh` で `assemble.py` の既定へ戻る。`bgm.py mix` が `bgm.yaml` から復元する。
- **中黒を入れすぎない。** 「オープン・エス・エス・エル」は不自然。
- **演技は「効く欄」だけで振る。** 文末の記号（`！` `？`）・`speed`・`pause_before`・
  `volume`。`emotion` は neutral かそうでないかの粗いスイッチ。`pitch`・`intonation`・
  `subtext`・`intensity` は音が動かない（semantic-audio-loom の `docs/resolve.md`）。
- **行は文の切れ目で割る。** 長い行は記号も効かない。字幕の折り返しは字数で決まるので、
  27 字を超える行は先に割る。
- **表情シートは 4列×2行の 8 マス・背景透過。** 差し替えたら `mouth_offset` を測り直す
  （`references/sheets/README.md`）。
- **チャイムは打音が頭から 1.4 秒以内に来るもの。** `assemble.py` は `chime.wav` を
  1.4 秒に切って章の頭へ置く。生成音の打音が遅いと、切った所に打音が残らず無音になる
  （『ハッブルの鏡』では 1.55 秒の打音を先頭へ切り出した）。`scriptcheck.py` は
  `chapters.yaml` があるのに `assets/sfx/chime.wav` が無いとき警告する。
- **置き場を移したら `tools/check_layout.py`。** 古い綴りが文書に残っていないか、
  `schemas/` が実物に通るかを見る。

## 言語

**日本語のみ。** 台本を英語や中国語で書けば同じ手順で焼けるが、仕組みとしての
翻訳・言語切替は持たない（`locales/` も `README-xx.md` も置かない）。

## 前提

- `ffmpeg`
- venv `$HOME/sonic-loom-spike/venv_tsukasa`（Pillow・numpy・scipy・PyYAML）
- 隣に `semantic-audio-loom`（声と組み立ての正本）。`SAL=` で場所を変えられる
