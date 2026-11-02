---
name: guide-bgm
description: 話の内容に合わせて敷き音（BGM）を毎回作る。台本・章から bgm.yaml の意図を書き、engine/bgm.py で MusicGen の 30 秒 × 数本をクロスフェードし、会話の約 13 dB 下・浅い ducking で混ぜる。make.sh は bgm.yaml があれば自動で生成とミックスを行い、mix.yaml の -30/14 を台本側の値へ戻す。
argument-hint: '作品の置き場。例: projects/<作品>'
---

# guide-bgm — 話に合わせて、敷き音を作る

BGM は毎回、その話から作る。**既製の曲を選ばない。** 意図は `bgm.yaml` に残し、
音は `engine/bgm.py` が semantic-audio-loom の MusicGen で作る。

出力は `projects/<作品>/bgm.yaml` と `projects/<作品>/assets/bgm/underlay.wav`。
`engine/make.sh` は `bgm.yaml` があれば、生成（不足・変更時）とミックスを自動で行う。

## 手順

1. **下書きを出す。**
   ```
   <venv> engine/bgm.py suggest --project projects/<作品> --out projects/<作品>/bgm.yaml
   ```
   章題と頻出語がコメントで出る。**prompt は英語で、話の内容に合わせて書き直す。**
   MusicGen は英語しか読まない。

2. **意図を決める。** `references/bgm-intent.md` の目安で、次を決める。
   - `prompt` … 音の説明（楽器・質感・気分・禁止事項）
   - `mood` … 2〜4 語
   - `duration` … 90 秒で足りる（`assemble.py` が全体長へ継ぎ足す）
   - `seeds` … `auto`（prompt から決定的）か、手で振った 3 本
   - `mix.gain_db` / `mix.duck` … 既定は **−8 dB / 3 dB**

3. **生成を確かめる。**
   ```
   <venv> engine/bgm.py generate --project projects/<作品> --dry-run
   <venv> engine/bgm.py generate --project projects/<作品>
   ```
   入力（prompt・シード・分割・クロスフェード・利得）が変わらなければ飛ぶ。
   作り直すなら `--force`、または `BGM=force ./engine/make.sh ...`。

4. **焼く。** `engine/make.sh` が、組み立ての前に生成し、`assemble.py --no-render` の
   あとに `engine/bgm.py mix` を 1 回だけ呼ぶ。**mix.yaml を手で直さない。**
   - `BGM=auto`（既定）… 入力が変わったときだけ生成
   - `BGM=force` / `BGM=1` … 毎回生成
   - `BGM=0` … BGM の段を全部飛ばす

5. **聞く。** 会話が始まってから 10 秒、章の変わり目、最後の無音を聴く。
   BGM が「流れている」と分かるか。会話を邪魔していないか。

## 音の選び方

- **持続音（パッド）を選ぶ。** スパースなピアノは音と音の間が無音になり、
  ducking も重なって消える。
- **打楽器・声・大きな展開を入れない。** 解説の下で鳴るもの。
- **章ごとに曲を変えない。** 1 本を全体に敷く。章は声と間で立てる。
- **不安は、音量ではなく和音で出す。** 音量を上げると会話とぶつかる。

## ミックスの目安

- 会話 RMS の **13〜15 dB 下**（実測: 会話 −27 dBFS に対し BGM −40 dBFS）。
- ducking は **3〜4 dB**。深いと BGM が消える。
- `assemble.py` の既定は bed −30 dB / duck 14 dB。`bgm.yaml` の `mix` が
  それを上書きする。**この上書きが、make.sh のたびに音量が戻る問題の直し。**

## 参照

- 意図の書き方・実測値 → `references/bgm-intent.md`
- 音の生成（正本） → `semantic-audio-loom` の `providers/musicgen.py` と `bin/mix.py`
