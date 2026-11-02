---
name: guide-script
description: 設計と人物から台本を書き、評議会の 8 次元評価に掛け、弱点を直して再評価する往復を回す。版ごとに下書きと評価 JSON を残し、平均 60 を超えた最高版を採用して script.yaml / video.yaml / chapters.yaml へ起こす。engine/review.py で採点を記録し、engine/scriptcheck.py で参照を確かめる。
argument-hint: '作品の置き場。例: projects/<作品>'
---

# guide-script — 書いて、評価して、直す

台本は一発で書かない。**生成 → 評価 → 改稿**を、版を残しながら回す。
評価は独立した 8 体の評議会。採用は**平均 60 を超えた最高版**で、最後の版とは限らない。

入力は `design.md` と `persona.yaml`。出力は採用版の `台本.md` と、
焼ける形の `script.yaml` / `video.yaml` / `chapters.yaml`。

## 手順

1. **人物票を読む。**
   ```
   <venv> engine/persona.py brief --cast <キャスト>
   ```
   これをプロンプトの冒頭に置く。台本を書く間、人物の正本はこれだけ。

2. **下書きを書く。** `projects/<作品>/review/drafts/vN.md` に、**台本だけ**を書く。
   制作メモ・評価への言い訳・章番号の説明は入れない。v1 から始める。

3. **評議会に掛ける。** `story-council` の 8 体（`lang: ja`）に、本文を**インライン**で渡す。
   `hook / plot-architecture / reader-experience / prose-style / admiration /
   anti-generic-story-filter / theme-resonance / emotional-power` の `-ja`。
   題・作者を外して渡す（二重盲検）。評価者ごとに JSON を
   `projects/<作品>/review/reports/vN/<評価者>.json` に保存する。

4. **JSON を確かめる。**
   ```
   <venv> engine/review.py validate --project projects/<作品> --version vN
   ```
   不正なら同じ評価者へ、エラーを添えて 3 回まで再依頼する。3 回で通らなければ
   `excluded` として理由を残す（黙って落とさない）。

5. **採点を記録して、表を見る。**
   ```
   <venv> engine/review.py record --project projects/<作品>
   <venv> engine/review.py table  --project projects/<作品>
   ```
   平均が 60 以下なら 6 へ。60 を超えたら、**それまでの最高版と比べて**採用を決める。

6. **直す。** 低い 2 次元（と 50 未満の次元）に絞る。高い次元は触らない。
   直したら vN+1 を書き、**新しい独立した 8 体**で採り直す。同じ評価者に
   「直ったか」を聞かない（採点が甘くなる）。

7. **採用する。**
   ```
   <venv> engine/review.py record --project projects/<作品> --adopted vN
   ```
   採用版を `projects/<作品>/台本.md` に写す。採用しなかった版も `review/drafts/` に残す。

8. **焼ける形へ起こす。** `script.yaml` / `video.yaml` / `chapters.yaml` を作る。
   起こし方は下の「YAML へ起こす」。最後に必ず:
   ```
   <venv> engine/scriptcheck.py --project projects/<作品>
   ```

9. **読みと BGM へ。** [guide-reading](../guide-reading/SKILL.md) →
   [guide-bgm](../guide-bgm/SKILL.md) → `engine/make.sh`。

## YAML へ起こす

- **1 cue = 1 文**（長くても息継ぎ 1 回）。`name` は `c001` から連番。
- **`……` だけの行は cue にしない。** 声を持たない行は音にならず、`build_voice.py` が
  落ちる。その間は次の cue の `pause_before` に畳む（0.6 秒の沈黙なら次の行へ +0.6）。
- `character` は `persona.yaml` / `cast.yaml` の id。固有名は書かない。
- `line` は**字幕に出したい文**。読みは `reading.yaml` が別に持つ（guide-reading）。
- `pause_before` / `speed` は、効かせたい所だけ。全部に書くと演技が平坦になる。
- **字幕は 27 字以内。** 超える行は文の切れ目で割る。割れないなら文を短くする。
- `video.yaml` の `chapters` は章の頭の cue。`chapters.yaml` は同じ cue の配列
  （音のチャイム）。**両方を揃える。**
- `display` は、`line` と字幕を変えたい cue だけ。読みの段が無い作品では必須になる。

## 評価の読み方

- **平均だけを見ない。** 分散が大きい版は、評価者の見方が割れている。割れは弱点の在処。
- **prose-style と anti-generic-story-filter は最後まで残りやすい。** 解説動画では、
  事例が等しい重みで並ぶと anti-generic が落ちる。章ごとに重さを変える。
- **評価者を替えても平均は ±3 点ほど動く。** 1 点の差で採否を決めない。
- 評価 JSON の `caveats` / `excluded` は消さない。次の版の判断材料になる。

## やらないこと

- 評価者に題・作者・採用予定を伝える。
- 平均を上げるために、評価者の弱点だけをなぞる（作品が評価に最適化される）。
- 60 を超えた最後の版を、無条件に採用する。**最高版を採る。**
- Markdown から YAML への自動変換。文の切れ目と cue 名は意味判断なので、ここで行う。

## 参照

- 往復の詳細・評価者の渡し方・版の残し方 → `references/loop.md`
- 設計 → [guide-design](../guide-design/SKILL.md)
- 人物 → [guide-cast](../guide-cast/SKILL.md)
