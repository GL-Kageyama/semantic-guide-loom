# semantic-guide-loom

**意味のある台本から、説明の映像を焼く。** 解説動画・社内の説明動画・研修の導入——
「人が見て分かる」映像を、AI の映像生成を使わずに、決定的に組み立てる。

掛け合いでも、語りだけでもよい。**型（template）を替えれば、同じ台本が別の絵になる。**

## 何が決まるのか

| 決めること | どこで決めるか |
| --- | --- |
| 何を、どの順で話すか | `script.yaml`（音の台本）× `video.yaml`（映像の台本） |
| 誰が声を出すか、どう演じるか | `script.yaml` の `character` と演技の欄 |
| 誰が画面に居るか | `casts/<名前>.cast.yaml` |
| どう見えるか（色・位置・間合い・並べ方） | `templates/<型>/` |
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

## 使い方

```bash
# 端から端まで
./engine/make.sh works/making-a-guide

# 1 枚だけ見る（数を詰めるとき）
./engine/make.sh works/making-a-guide --still 40

# 音はそのままで、絵だけ焼き直す
SKIP_VOICE=1 SKIP_ASSETS=1 ./engine/make.sh works/making-a-guide
```

- `FORCE=1` … 声を作り直す。**参照音声や `voice_fx.yaml` を変えたときはこれが要る**
  （既定のままでは既存の WAV を飛ばす）。
- 作品はこのリポジトリに無くてよい。`script.yaml` と `video.yaml` のある所を指す。
  `./engine/make.sh ../semantic-audio-loom/projects/longform/cyber-basics`

必要なもの: `ffmpeg`、Pillow・numpy・scipy・PyYAML（`$HOME/sonic-loom-spike/venv_tsukasa`）、
隣に `semantic-audio-loom`（声と組み立ての道具はそこが正本）。

clone したら一度 `git lfs pull`。表情シート（`sheets/`）と焼いた動画（`out/`）は LFS に在る。

## 型

| 型 | 見た目 | 使うとき |
| --- | --- | --- |
| `dialogue-bust` | 左に人・右に相棒、中央に章の札、下に字幕 | 掛け合いで説明する。4〜5 分に耐える |
| `narrate-slide` | 左に章の題と箇条書き、下に字幕。人物なし | 社内説明・研修。1 章 = 1 枚で読み物として立つ |

型は「数」（`template.yaml`）と「並べ方」（`engine/layouts/*.py`）に分かれている。
**色違い・位置違いの型は YAML 1 枚で足りる。** 並べ方が違う型はモジュールを 1 本足す。
手順は [docs/template-contract.md](docs/template-contract.md)。

`out/` に見本が 2 本。`cyber-basics.mp4`（掛け合い型・1280×720・4 分 47 秒）と
`making-a-guide.mp4`（語り型・1920×1080・53 秒）。

## 作品の書き方

```
works/<作品名>/
  script.yaml     何を、どの順で、誰が、どう話すか（音の台本）
  video.yaml      題・章・字幕の表記・型・キャスト（映像の台本）
  chapters.yaml   章の頭の cue（音のチャイム）
```

`video.yaml` の `template:` と `cast:` が、どの型でどのキャストを置くかを名乗る。
人物を置かない型は `cast:` を書かない。

ファイルの契約は [docs/contract.md](docs/contract.md)。

## 構成

```
engine/
  make.sh              5 段を通す
  prepare_assets.py    表情シート → 素材
  export_timeline.py   mix.yaml → timeline.json
  render.py            入口（読む・型を選ぶ・焼く）
  common.py            尺度・色・書体・文字・素材（型に依らない）
  layouts/
    dialogue_bust.py   掛け合い・胸像型の並べ方
    narrate_slide.py   語り・スライド型の並べ方
templates/<型>/template.yaml
casts/<キャスト>.cast.yaml
sheets/                表情シート（入力。Git LFS）
works/<作品>/
out/<作品>.mp4         焼いた動画（成果物。Git LFS）
build/<作品>/          中間物（.gitignore。焼き直せば戻る）
docs/                  契約と型の説明
```

## 決まりごと

- **時刻は音から取る。** `pause_before` を足し直すと 1 コマずつずれる。
- **字幕は `video.yaml` の `display`。** `line` は読みのためにカタカナで書く。
- **読み違えはルビで塞ぐ**（`漢字《かな》`）。音だけ仮名になり、字幕は原表記のまま。
- **1 コマは状態を持たない。** 同じ時刻なら同じ絵が出る。
- **型は作品を知らない。** 特定の題・人数・章の数を型に書かない。

## ライセンス

MIT
