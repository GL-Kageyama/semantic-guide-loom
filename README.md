# semantic-guide-loom

<p align="center">
  <img src="assets/repo-hero.png" width="100%" alt="semantic-guide-loom">
</p>

**意味のある台本から、説明の映像を焼く。** 解説動画・社内の説明動画・研修の導入——
「人が見て分かる」映像を、AI の映像生成を使わずに、決定的に組み立てる。

掛け合いでも、語りだけでもよい。**型（template）を替えれば、同じ台本が別の絵になる。**

## 何が決まるのか

| 決めること | どこで決めるか |
| --- | --- |
| 何を、どの順で話すか | `design.md`（設計）→ `script.yaml`（音の台本）× `video.yaml`（映像の台本） |
| 誰が声を出すか、どう演じるか | `script.yaml` の `character` と演技の欄 |
| 誰が話し、どう喋るか | `characters/<名前>.persona.yaml`（言葉の設定） |
| 誰が画面に居るか | `characters/<名前>.cast.yaml`（画面の設定） |
| 声にどう読ませるか | `reading.yaml`（かな）。字幕は `video.yaml` の `display` が持つ |
| 敷き音 | `bgm.yaml`（意図とミックス）→ `assets/bgm/underlay.wav` |
| どう見えるか（色・位置・間合い・並べ方） | `references/templates/<型>/` × `engine/layouts/` |
| 時刻 | **音の実尺**。台本から数え直さない |

## 5 つの段

```
1 素材   prepare_assets.py   表情シート → 口の 3 状態の切り抜き（型が人物を置くときだけ）
2 声     build_voice.py      1 行 → 1 つの WAV          （semantic-audio-loom）
3 組み立て assemble.py       間・声量・章の印 → 1 本の WAV（semantic-audio-loom）
4 時刻   export_timeline.py  mix.yaml の実尺 → timeline.json
5 描画   render.py           Pillow で 1 コマずつ → ffmpeg で 1 本
```

`engine/make.sh` が 5 つを順に通す。**矢印は一方向**——絵は音の実尺を読む。音は絵を知らない。
ゆえに台本を変えても、絵の側の時刻を手で直す必要はない。

`reading.yaml` があるときは、2 の前に `engine/reading.py stage` が `build/<作品>/` に
舞台を作る（`line` を読みに、`display` に原表記を）。`bgm.yaml` があるときは、3 で
`engine/bgm.py` が生成とミックスを行う。**どちらも無ければ、従来の 5 段のまま。**

## 台本を、設計から作る

判断が要る工程はスキル、決定的にできる工程は `engine/` の道具。**engine は LLM を呼ばない。**

| 段 | スキル | 作るもの | 道具 |
| --- | --- | --- | --- |
| 設計 | `guide-design` | `design.md`（約束・章・事実の柱・役割） | story-council（plot モード） |
| 人物 | `guide-cast` | `characters/<キャスト>.persona.yaml` | `engine/persona.py` |
| 台本 | `guide-script` | `台本.md` → `script.yaml` / `video.yaml` / `chapters.yaml` | story-council（8 次元）・`engine/review.py`・`engine/scriptcheck.py` |
| 読み | `guide-reading` | `reading.yaml` | `engine/reading.py` |
| BGM | `guide-bgm` | `bgm.yaml` → `assets/bgm/underlay.wav` | `engine/bgm.py` |
| 焼く | `semantic-guide-loom` | `renders/<作品>.mp4` | `engine/make.sh` |

- **台本は平均 60 超の最高版を採る。** 版ごとに `review/drafts/vN.md` と
  `review/reports/vN/*.json` を残し、`engine/review.py record` が `review/scores.yaml` に書く。
- **ペルソナとキャストを混ぜない。** `persona.yaml` は話し方、`cast.yaml` は画面。
  名前はどちらもデータで、コードには書かない。
- **読みは音のためだけ。** 字幕・章題には渡さない。

## 使い方

```bash
# 端から端まで
./engine/make.sh projects/making-a-guide

# 1 枚だけ見る（数を詰めるとき）
./engine/make.sh projects/making-a-guide --still 40

# 音はそのままで、絵だけ焼き直す
SKIP_VOICE=1 SKIP_ASSETS=1 ./engine/make.sh projects/making-a-guide
```

- `FORCE=1` … 声を作り直す。**参照音声や `voice_fx.yaml` を変えたときはこれが要る**
  （既定のままでは既存の WAV を飛ばす）。
- `BGM=auto`（既定）… `bgm.yaml` があれば、入力が変わったときだけ敷き音を作り直す。
- `BGM=force`（または `BGM=1`）… 毎回作り直す。`BGM=0` … BGM の段を飛ばす。
- 作品はこのリポジトリに無くてよい。`script.yaml` と `video.yaml` のある所を指す。
- **clone しただけでも、声を作らずに同じ絵が出せる。** 見本 2 本の資材（声・効果音・
  BGM）は `projects/<作品>/assets/` に入っているから、声の段を飛ばせばよい。

  ```bash
  SKIP_VOICE=1 ./engine/make.sh projects/cyber-basics
  ```

必要なもの: `ffmpeg`、Pillow・numpy・scipy・PyYAML（`$HOME/sonic-loom-spike/venv_tsukasa`）、
隣に `semantic-audio-loom`（声と組み立ての道具はそこが正本）。

clone したら一度 `git lfs pull`。表情シート（`references/sheets/`）・資材
（`projects/<作品>/assets/`）・焼いた動画（`projects/<作品>/renders/`）は LFS に在る。

## 型

| 型 | 見た目 | 使うとき |
| --- | --- | --- |
| `dialogue-bust` | 左に人・右に相棒、中央に章の札、下に字幕 | 掛け合いで説明する。4〜5 分に耐える |
| `narrate-slide` | 左に章の題と箇条書き、下に字幕。人物なし | 社内説明・研修。1 章 = 1 枚で読み物として立つ |

型は「数」（`references/templates/<型>/template.yaml`）と「並べ方」
（`engine/layouts/*.py`）に分かれている。**色違い・位置違いの型は YAML 1 枚で足りる。**
並べ方が違う型はモジュールを 1 本足す。手順は [docs/template-contract.md](docs/template-contract.md)。

見本は 2 本。`projects/cyber-basics/renders/cyber-basics.mp4`（掛け合い型・1280×720・
4 分 47 秒）と `projects/making-a-guide/renders/making-a-guide.mp4`
（語り型・1920×1080・53 秒）。

## 作品の書き方

```
projects/<作品名>/
  design.md       題材・約束・章・事実の柱（任意。設計から作るとき）
  reading.yaml    cue → 声に読ませる読み（任意。無ければ line をそのまま読む）
  bgm.yaml        敷き音の意図とミックス（任意。無ければ BGM の段を飛ばす）
  script.yaml     何を、どの順で、誰が、どう話すか（音の台本）
  video.yaml      題・章・字幕の表記・型・キャスト（映像の台本）
  chapters.yaml   章の頭の cue（音のチャイム）
  voice_fx.yaml   声に掛ける効果（任意）
  review/         台本の版・評価・採用の記録（任意。設計から作るとき）
  assets/
    voice/        1 行 1 つの声（+ .params.yaml）— 入力
    sfx/  bgm/    効果音・敷き音 — 入力
  renders/        焼いた動画 — 成果物（Git LFS）
```

`assets/` の中で `assemble.py` が作るもの（`voice_trim/` `voice_fx/` `assets/renders/`
`*_tiled.wav` `*_short.wav`）と `mix.yaml` は派生ゆえ `.gitignore`。
**作品の `renders/`（動画）とは別の置き場**であることに注意。

`video.yaml` の `template:` と `cast:` が、どの型でどのキャストを置くかを名乗る。
人物を置かない型は `cast:` を書かない。

ファイルの契約は [docs/contract.md](docs/contract.md)。

## 構成

```
.claude-plugin/        配布の manifest（plugin.json / marketplace.json）
.claude/skills/        install.sh --local が張る symlink
skills/
  semantic-guide-loom/SKILL.md   入口。焼く手順（スキルの本体）
  guide-design/        設計（design.md）
  guide-cast/          人物の言葉の設定（persona.yaml）
  guide-script/        台本の生成と評価の往復
  guide-reading/       読み（reading.yaml）
  guide-bgm/           敷き音（bgm.yaml）
engine/
  make.sh              5 段を通す
  prepare_assets.py    表情シート → 素材
  persona.py           persona の検査・人物票・既存台本の分析
  review.py            評議会の採点を集計・記録
  reading.py           読みの下書き・監査・ビルド用の舞台
  scriptcheck.py       script / video / chapters / reading の整合
  bgm.py               敷き音の下書き・生成・ミックス
  export_timeline.py   mix.yaml → timeline.json
  render.py            入口（読む・型を選ぶ・焼く）
  common.py            尺度・色・書体・文字・素材（型に依らない）
  layouts/
    dialogue_bust.py   掛け合い・胸像型の並べ方
    narrate_slide.py   語り・スライド型の並べ方
references/templates/<型>/template.yaml   型の「数」
references/sheets/                        表情シート（入力。Git LFS）
characters/<キャスト>.cast.yaml   誰が画面に居るか
characters/<キャスト>.persona.yaml 誰がどう話すか
projects/<作品>/       台本・資材・焼いた動画（asset は Git LFS）
schemas/               video / template / cast / persona / reading / bgm の形
tools/
  check_layout.py      置き場の綴りと schemas を確かめる
docs/                  契約と型の説明
assets/repo-hero.png   この README の絵（git-lfs）
build/<作品>/          中間物（.gitignore。焼き直せば戻る）
```

## 言語

**このリポジトリは多言語対応をしない。** 台本・型・キャスト・文書は日本語だけ。

姉妹リポジトリ（`semantic-audio-loom` / `semantic-visual-loom`）は
`README-ja.md` / `README-zh.md`・`docs/*-ja.md`・`locales/` を持つが、ここには置かない。
理由は、このリポジトリの成果物が**日本語の音声と日本語の字幕**であること。台本を
英語や中国語で書けば同じ手順で焼ける（`script.yaml` の `line` と `video.yaml` の
`display` に、その言語の文を書くだけ）——が、**仕組みとしての翻訳・言語切替は作らない。**

多言語化は別の段に置く。取り込むときは、姉妹リポジトリと同じ 3 層
（ロケール JSON・言語別プロンプト・ミラーツリー）で入れる。

## 決まりごと

- **時刻は音から取る。** `pause_before` を足し直すと 1 コマずつずれる。
- **字幕は `video.yaml` の `display`。** `line` は声に読ませる形。
- **読み違えは `reading.yaml` で塞ぐ。** 字幕は原表記のまま（`display`）。
- **BGM の音量と ducking は `bgm.yaml` が持つ。** `mix.yaml` は手で直さない。
- **1 コマは状態を持たない。** 同じ時刻なら同じ絵が出る。
- **型は作品を知らない。** 特定の題・人数・章の数を型に書かない。
- **置き場を移したら `tools/check_layout.py`。** 古い綴りが文書に残っていないかを見る。

## ライセンス

MIT
