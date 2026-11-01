# semantic-guide-loom — プロジェクト指示

## 文書ルール

開発履歴（日付入りの変更経緯・過去の設計との比較・実測値）は README / docs に書かない。
履歴は `HISTORY.md` に一元化する。README / docs には**現在の情報だけ**を書く。

- `README.md` … 何をするものか・構成・使い方（概要のみ）
- `docs/` … 契約（`contract.md`）と型の作り方（`template-contract.md`）
- `HISTORY.md` … 開発履歴と実測値
- 設計の背景・未裁定の事項は**このリポジトリの外**（作者の手元）。配布物からリンクしない。

## 置き場（姉妹リポジトリに倣う）

`semantic-audio-loom` / `semantic-visual-loom` と同じ並びにする。中身の道具立ては違うが、
**同じ名のものが同じ場所に在る**ことを崩さない。

```
.claude-plugin/   skills/   references/   schemas/   characters/
projects/<作品>/   engine/   docs/   tools/   assets/repo-hero.png
```

- **作品は `projects/<作品>/` に閉じる。** 台本・資材・焼いた動画が 1 か所に入る
  （向こうは `projects/<project>/assets/` に音を置く。こちらも同じ）。
- **`engine/` はこのリポジトリの道具。** 姉妹の `bin/`・`engine/` に当たる。
- **`references/` は絵の側の資材**（型・表情シート）。向こうの `references/` は
  参照音声・様式で、意味は違うが「再利用する元」という役目は同じ。
- 置き場を移したら `tools/check_layout.py` を走らせる。古い綴りが残っていないか、
  `schemas/` が実物に通るかを見る。

**多言語対応はしない。** `README-ja.md` / `README-zh.md`・`docs/*-ja.md`・`locales/` を
置かない。台本を他言語で書けば焼けるが、**仕組みとしての翻訳・言語切替は作らない**
（README「言語」）。取り込むのは別の段。

## 固定方針（変更しない）

- **5 段の矢印は一方向。** 絵は音の実尺を読む。音は絵を知らない。時刻を台本から
  数え直す経路を作らない。
- **型は絵の側だけを持つ。** 意味（題・章・字幕・時刻）は作品が持つ。
  型に特定の題・人数・章の数を書かない。
- **登場人物はデータ。** コードに `mirai` のような固有名を書かない。
  名前は `characters/<名前>.cast.yaml` と `script.yaml` にしか出てこない。
- **1 コマは状態を持たない。** `draw_frame(t, fi)` は時刻だけから絵を決める。
  途中から焼いても同じ絵になること（`--still` / `--start`）を壊さない。
- **音の道具の正本は `semantic-audio-loom`。** 声（`build_voice.py`）と組み立て
  （`assemble.py`）はここへ写さない。このリポジトリはパスで呼ぶ。
- **`script.yaml` の形の正本も `semantic-audio-loom`。**
  `schemas/scene.schema.json`。ここへ写さない（写すと黙って古くなる）。
- **決定的であること。** 同じ台本・同じ素材から同じ絵が出る。時刻に乱数を使わない。

## 触ってはいけないもの

- **`semantic-audio-loom` の中身を書き換えない。** 読むのはよい。ただし
  `--assets` のように**後方互換な受け口を足す**のは可（既定の挙動を変えない）。
- **`distill-essence-engine` を触らない。**
- **`資料/`（作者の私的ノート）へのリンクを配布物に書かない。** clone した人に見えない。

## Git

- `git push` はユーザーが明示的に依頼した時だけ。
- コミットメッセージ末尾に `Co-Authored-By: Claude Code <noreply@anthropic.com>`。
- **`git add -A` は使わない。** 触ったパスだけを add する。
- **音声と画像は Git LFS**：`*.wav` `*.mp3` `*.m4a` `*.flac` `*.ogg` `*.mp4` `*.png`
  `*.jpg` `*.jpeg`（`.gitattributes`）。テキストは対象外。
- **入れるのは「入力」と「成果物」、入れないのは「中間物」。** LFS で入れるのは
  `references/sheets/`（表情シート）・`projects/<作品>/assets/{voice,sfx,bgm}/`
  （原盤）・`projects/<作品>/renders/*.mp4`（焼いた動画）。入れないのは `build/`・
  `projects/*/mix.yaml`・`projects/*/assets/voice_trim/`・`projects/*/assets/voice_fx/`・
  `projects/*/assets/renders/`・`projects/*/assets/bgm/*_tiled.wav`・
  `projects/*/assets/sfx/*_short.wav`（どれも焼き直せば戻る）。clone したら `git lfs pull`。

## 環境

- venv は `/Users/user/sonic-loom-spike/venv_tsukasa`（Pillow・numpy・scipy・PyYAML・
  semantic-audio-loom の依存）。素の `python3` では Pillow などが足りない。
  `tools/check_layout.py` だけは素の `python3` でも走る（`jsonschema` が無い環境では
  schemas の段を飛ばす）。
- `ffmpeg` が要る。
