# 使い方 — 走らせ方と道具

5 つの段は `engine/make.sh` が順に通す。**判断が要る工程はスキル、決定的にできる工程は
`engine/` の道具。** engine は LLM を呼ばない。

```
1 素材   prepare_assets.py   表情シート → 口の 3 状態の切り抜き（型が人物を置くときだけ）
2 声     build_voice.py      1 行 → 1 つの WAV          （semantic-audio-loom）
3 組み立て assemble.py       間・声量・章の印 → 1 本の WAV（semantic-audio-loom）
4 時刻   export_timeline.py  mix.yaml の実尺 → timeline.json
5 描画   render.py           Pillow で 1 コマずつ → ffmpeg で 1 本
```

**矢印は一方向。** 絵は音の実尺を読む。音は絵を知らない。ゆえに台本を変えても、
絵の側の時刻を手で直す必要はない。

## 必要なもの

- `ffmpeg`
- Pillow・numpy・scipy・PyYAML（venv: `$HOME/sonic-loom-spike/venv_tsukasa`）
- 隣に `semantic-audio-loom`（声と組み立ての正本。このリポジトリに写さない）

`PY` と `SAL` で場所を差せる。

## 端から端まで

```bash
./engine/make.sh projects/making-a-guide

# 1 枚だけ見る（数を詰めるとき）
./engine/make.sh projects/making-a-guide --still 40

# 音はそのままで、絵だけ焼き直す
SKIP_VOICE=1 SKIP_ASSETS=1 ./engine/make.sh projects/making-a-guide
```

clone しただけでも、声を作らずに同じ絵が出せる。見本 2 本の資材（声・効果音・BGM）は
`projects/<作品>/assets/` に入っているから、声の段を飛ばせばよい。

```bash
git lfs pull
SKIP_VOICE=1 ./engine/make.sh projects/cyber-basics
```

## 環境変数

| 変数 | 既定 | 何 |
| --- | --- | --- |
| `FORCE=1` | — | 声を作り直す。**参照音声や `voice_fx.yaml` を変えたときはこれが要る**（既定では既存の WAV を飛ばす） |
| `SKIP_ASSETS=1` | — | 表情シートの切り出しを飛ばす |
| `SKIP_VOICE=1` | — | 声の生成を飛ばす（台本を変えていないとき） |
| `BGM=auto` | `auto` | 敷き音を作り直すか。`auto`＝入力が変わったときだけ／`force`（`1`）＝毎回／`0`＝飛ばす |
| `STRICT=1` | — | 事前検査の警告も失敗として扱う |
| `PY` | `$HOME/sonic-loom-spike/venv_tsukasa/bin/python` | venv の python |
| `SAL` | 隣の `semantic-audio-loom` | 音の道具箱 |

**作品はこのリポジトリに無くてもよい。** `script.yaml` と `video.yaml` のある
ディレクトリならどこでも指せる。その場合、音の資材は `projects/<作品>/assets/` が
無ければ `build/<作品>/audio` に作られ、動画は作品の `renders/` へ出る。

## 段ごとの道具

### 0 事前検査（焼く前）

```bash
engine/scriptcheck.py --project projects/<作品>            # 形・所属・順序・容量・fact の参照
engine/scriptcheck.py --project projects/<作品> --json     # 機械可読
engine/acting.py audit --project projects/<作品>           # 演技の欄の参照切れ・網羅・単調さ
```

`make.sh` はこの 2 つを最初に走らせる。演技の欄が無い古い作品も通す（警告だけ）。
`STRICT=1` で警告も失敗にする。

### 1 素材

```bash
engine/prepare_assets.py --work projects/<作品> --out build/<作品>/assets
```

`video.yaml` の `cast` を読み、`references/sheets/` の表情シートから口の 3 状態を
切り出す。人物を置かない型はこの段を飛ばす。結果は `build/<作品>/assets/faces.json`
（派生）。

### 2 声

```bash
# 正本は semantic-audio-loom。make.sh はパスで呼ぶ
PYTHONPATH="$SAL" "$PY" "$SAL/projects/longform/explainer/build_voice.py" \
    --dir <台本の場所> --assets projects/<作品>/assets
```

`reading.yaml` があるときは、その前に `engine/reading.py stage` が
`build/<作品>/` に舞台を作る（[reading.md](reading.md)）。

### 3 組み立て

```bash
PYTHONPATH="$SAL" "$PY" "$SAL/projects/longform/assemble.py" \
    --dir <台本の場所> --assets projects/<作品>/assets
```

間・声量・章のチャイムを掛け、`mix.yaml` と 1 本の WAV を書く。`bgm.yaml` がある
作品は、この段の前後に `engine/bgm.py generate` と `engine/bgm.py mix` が挟まる
（[bgm.md](bgm.md)）。

### 4 時刻

```bash
engine/export_timeline.py --project projects/<作品> \
    --out build/<作品>/timeline.json --audio projects/<作品>/assets/renders/<作品>.wav
```

`mix.yaml` の voice stem の実尺から `timeline.json` を作る。**台本から数え直さない。**
実尺が要る検査（詳細カードの可視時間など）は、ここで警告として出る
（[timeline.md](timeline.md)）。

### 5 描画

```bash
engine/render.py --timeline build/<作品>/timeline.json \
    --out projects/<作品>/renders/<作品>.mp4

engine/render.py --timeline build/<作品>/timeline.json --still 40 --out /tmp/frame.png
```

| 引数 | 何 |
| --- | --- |
| `--timeline` | `timeline.json`（既定は `build/<作品>/timeline.json`） |
| `--template` / `--cast` | 型・キャストの名を上書き（既定は `timeline.json` の値） |
| `--out` | 書き先。省略時は `<project>/renders/<name>.mp4` |
| `--start` / `--duration` | 途中から焼く（秒） |
| `--still` | その時刻の 1 枚だけを `--out` へ書く |
| `--fps` / `--crf` / `--preset` | ffmpeg とコマ数（既定は `timeline.json` の fps） |

**1 コマは状態を持たない。** 同じ時刻なら同じ絵が出る。`--start` と `--still` が
その検算になる。

## そのほかの道具

```bash
engine/reading.py draft  --project projects/<作品>        # reading.yaml の下書き
engine/reading.py audit  --project projects/<作品>        # 残存漢字・数字・%・Latin を見る
engine/bgm.py suggest    --project projects/<作品>        # bgm.yaml の下書き
engine/persona.py check  --project projects/<作品>        # 人物票・関係・cast の語彙
engine/persona.py brief  --project projects/<作品>        # 台本書きに渡す人物票
engine/persona.py analyze --project projects/<作品>       # 既存台本から話し方の実測
engine/acting.py report  --project projects/<作品> --out <YAML> --version vN
engine/review.py table   --project projects/<作品>        # 評議会の版ごとの平均と採否
engine/viewer.py record  --project projects/<作品> --version vN   # 視聴者の門
tools/check_layout.py                                     # 置き場の綴りと schemas
```

各段の意味は [placement.md](placement.md) と、下の「ドキュメント」から辿る。
