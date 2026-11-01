# semantic-guide-loom — プロジェクト指示

## 文書ルール

開発履歴（日付入りの変更経緯・過去の設計との比較・実測値）は README / docs に書かない。
履歴は `HISTORY.md` に一元化する。README / docs には**現在の情報だけ**を書く。

- `README.md` … 何をするものか・構成・使い方（概要のみ）
- `docs/` … 契約（`contract.md`）と型の作り方（`template-contract.md`）
- `HISTORY.md` … 開発履歴と実測値
- 設計の背景・未裁定の事項は**このリポジトリの外**（作者の手元）。配布物からリンクしない。

## 固定方針（変更しない）

- **5 段の矢印は一方向。** 絵は音の実尺を読む。音は絵を知らない。時刻を台本から
  数え直す経路を作らない。
- **型は絵の側だけを持つ。** 意味（題・章・字幕・時刻）は作品が持つ。
  型に特定の題・人数・章の数を書かない。
- **登場人物はデータ。** コードに `mirai` のような固有名を書かない。
  名前は `casts/<名前>.cast.yaml` と `script.yaml` にしか出てこない。
- **1 コマは状態を持たない。** `draw_frame(t, fi)` は時刻だけから絵を決める。
  途中から焼いても同じ絵になること（`--still` / `--start`）を壊さない。
- **音の道具の正本は `semantic-audio-loom`。** 声（`build_voice.py`）と組み立て
  （`assemble.py`）はここへ写さない。このリポジトリはパスで呼ぶ。
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
- **入れないのは `build/` だけ**（中間物。焼き直せば戻る）。**`sheets/`（入力）と
  `out/`（成果物）は LFS で入れる。** clone したら `git lfs pull`。
  理由は `sheets/README.md`。

## 環境

- venv は `/Users/user/sonic-loom-spike/venv_tsukasa`（Pillow・numpy・scipy・PyYAML・
  semantic-audio-loom の依存）。素の `python3` では足りない。
- `ffmpeg` が要る。
