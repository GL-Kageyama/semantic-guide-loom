# semantic-guide-loom

<p align="center">
  <img src="assets/repo-hero.png" width="100%" alt="semantic-guide-loom">
</p>

**テーマが、台本になり、映像になる。**

テーマを調べ、設計し、台本を書く。あとはそれが、声になり、映像になる。

生成はローカルPCで完結する。

## 5 つの段

```
1 素材   prepare_assets.py   表情シート → 口の 3 状態の切り抜き（人物を置く型だけ）
2 声     build_voice.py      1 行 → 1 つの WAV          （semantic-audio-loom）
3 組み立て assemble.py       間・声量・章の印 → 1 本の WAV（semantic-audio-loom）
4 時刻   export_timeline.py  mix.yaml の実尺 → timeline.json
5 描画   render.py           Pillow で 1 コマずつ → ffmpeg で 1 本
```

`engine/make.sh` が 5 つを順に通す。**矢印は一方向**——絵は音の実尺を読む。音は絵を
知らない。ゆえに台本を変えても、絵の側の時刻を手で直す必要はない。

**0 段（調査）** と `reading.yaml`・`bgm.yaml` は任意。詳細は
[docs/usage.md](docs/usage.md) と [docs/design.md](docs/design.md)。

## クイックスタート

```bash
git lfs pull                                     # 表情シート・声・焼いた動画は LFS
./engine/make.sh projects/making-a-guide         # 端から端まで
./engine/make.sh projects/making-a-guide --still 40   # 1 枚だけ見る
SKIP_VOICE=1 SKIP_ASSETS=1 ./engine/make.sh projects/cyber-basics  # 絵だけ焼き直す
```

必要なもの: `ffmpeg`、Pillow・numpy・scipy・PyYAML（`$HOME/sonic-loom-spike/venv_tsukasa`）、
隣に `semantic-audio-loom`（声と組み立ての正本）。**clone しただけでも、声を作らずに
同じ絵が出せる**（見本の資材が入っているので `SKIP_VOICE=1`）。
環境変数・段ごとの CLI は [docs/usage.md](docs/usage.md)。

## 型

| 型 | 見た目 | 使うとき |
| --- | --- | --- |
| `dialogue-bust` | 左に人・右に相棒、中央に章の札、下に字幕。詳細カードが切り替わる | 掛け合いで説明する |
| `narrate-slide` | 左に章の題と箇条書き、下に字幕。人物なし | 社内説明・研修 |

型は「数」（`references/templates/<型>/template.yaml`）と「並べ方」
（`engine/layouts/*.py`）に分かれる。足し方は [docs/templates.md](docs/templates.md)。

## 作品の書き方

**作品は `projects/<作品>/` に閉じる。** `script.yaml`（音の台本）・`video.yaml`
（映像の台本）・`assets/`・`renders/` が 1 か所に入る。`video.yaml` の `template:` と
`cast:` が、どの型で誰を置くかを名乗る。

ファイルの契約は [docs/script.md](docs/script.md) から、
入力・成果物・中間物の線引きは [docs/placement.md](docs/placement.md) から辿る。
台本を設計から作るときは、`skills/semantic-guide-loom/SKILL.md` の段に従う。

## 構成

```
skills/       判断が要る工程（調査・設計・人物・台本・演技・読み・BGM）
engine/       決定的な道具（LLM を呼ばない）
references/   型と表情シート
characters/   人物票・関係・キャスト
projects/     作品（台本・資材・焼いた動画）
schemas/      JSON Schema
docs/         契約と手順
tools/        置き場の検査
```

詳しい並びは [docs/placement.md](docs/placement.md)。

## Git（LFS）

音声と画像（`*.wav` `*.mp4` `*.png` など）は **Git LFS** に入る。テキストは普通の blob。
LFS に入るのは表情シート・声と効果音と敷き音の原盤・焼いた動画の 3 つ。
`git-lfs` の無い clone は実体を降ろさないので、後から `git lfs pull`。
規則と置き場は [docs/placement.md](docs/placement.md)。

## ドキュメント

| 文書 | 内容 |
| --- | --- |
| [docs/usage.md](docs/usage.md) | 走らせ方・環境変数・段ごとの道具・CLI |
| [docs/placement.md](docs/placement.md) | 置き場・入力／成果物／中間物・Git LFS |
| [docs/design.md](docs/design.md) | 設計（`design.md`・説明の鎖） |
| [docs/research.md](docs/research.md) | 調査の台帳（`sources.yaml` / `facts.yaml`） |
| [docs/script.md](docs/script.md) | `script.yaml`・演技の欄・`voice_fx.yaml` |
| [docs/video.md](docs/video.md) | `video.yaml`・`chapters.yaml` |
| [docs/reading.md](docs/reading.md) | 読み（`reading.yaml`）と舞台 |
| [docs/bgm.md](docs/bgm.md) | 敷き音（`bgm.yaml`）とミックス |
| [docs/characters.md](docs/characters.md) | 人物票・関係・キャスト・表情シート |
| [docs/acting.md](docs/acting.md) | 演技の欄・検査・描画 |
| [docs/templates.md](docs/templates.md) | 型（`template.yaml`・`layouts`・足し方） |
| [docs/timeline.md](docs/timeline.md) | `mix.yaml` / `timeline.json`（継ぎ目） |
| [docs/review.md](docs/review.md) | 二つの台帳（文学評議会と視聴者の門） |
| [HISTORY.md](HISTORY.md) | 開発履歴・実測値 |

## 言語

**日本語のみ。** 多言語化はしない（`README-xx.md` も `locales/` も置かない）。
台本を他言語で書けば焼けるが、仕組みとしての翻訳・言語切替は持たない。

## 状態

**5 段すべてが動く。** 見本は 4 本。

| 作品 | 型 | 画 | 尺 |
| --- | --- | --- | --- |
| `projects/cyber-basics/` | 掛け合い | 1280×720 | 4 分 47 秒 |
| `projects/making-a-guide/` | 語り | 1920×1080 | 51 秒 |
| `projects/black-swan-ai/` | 掛け合い | 1280×720 | 15 分 4 秒 |
| `projects/hubble-mirror/` | 掛け合い | 1280×720 | 17 分 14 秒 |

`hubble-mirror` は調査・設計・評価の往復まで通した作品。履歴は [HISTORY.md](HISTORY.md)。

## 決まりごと

- **時刻は音の実尺から取る。** 台本から数え直さない。
- **字幕は `video.yaml` の `display`。** `line` は声に読ませる形。
- **1 コマは状態を持たない。** 同じ時刻なら同じ絵が出る。
- **事実は台帳から引く。** `details[].fact` が `research/facts.yaml` の id を指す。
- **型は作品を知らない。** 特定の題・人数・章の数を型に書かない。

## ライセンス

MIT
