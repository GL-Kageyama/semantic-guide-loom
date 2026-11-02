---
name: guide-script
description: 設計と人物から台本を書き、評議会の評価に掛け、弱点を直して再評価する往復を回す。キャストの居る作品は 10 次元（既存 8 + character-depth + character-role）、語りだけの作品は 8 次元。版ごとに下書きと評価 JSON を残し、平均 60 を超えた最高版を採用して script.yaml / video.yaml / chapters.yaml へ起こす。engine/review.py で採点を記録・比較し、engine/scriptcheck.py で参照を確かめる。演技は guide-acting で付ける。
argument-hint: '作品の置き場。例: projects/<作品>'
---

# guide-script — 書いて、評価して、直す

台本は一発で書かない。**生成 → 評価 → 改稿**を、版を残しながら回す。
評価は独立した評議会。採用は**平均 60 を超えた最高版**で、最後の版とは限らない。

入力は `design.md`、人物票（`characters/<id>.character.yaml`）、
`review/acting/plan.md`。出力は採用版の `台本.md` と、演技を付けた
`script.yaml` / `video.yaml` / `chapters.yaml`。

## 手順

1. **人物票を全部読む。**
   ```
   <venv> engine/persona.py brief --cast <キャスト>
   ```
   全員ぶんをプロンプトの冒頭に置く。台本を書く間、人物の正本はこれだけ。
   `concept` / `contradiction` / `habits` / `speech` / `emotions` を、台詞の選び方へ翻訳する。

2. **演技の設計を読む。** `review/acting/plan.md`（guide-acting が作る）。
   章ごとの感情の弧、人物ごとの「漏らす／隠す」、山場と沈黙、反応の置き所。
   **演技を後付けにしない。** 台詞はこの弧の上で書く。

3. **下書きを書く。** `projects/<作品>/review/drafts/vN.md` に、**台本だけ**を書く。
   制作メモ・評価への言い訳・章番号の説明は入れない。v1 から始める。

4. **評議会に掛ける。**
   - キャストの居る作品 → **10 次元**。`-ja` の評価者 10 体。
     `hook / plot-architecture / reader-experience / prose-style / admiration /
     anti-generic-story-filter / theme-resonance / emotional-power` に、
     **`character-depth` と `character-role`** を足す。
   - 語りだけの作品 → 従来の **8 次元**。
   本文は**インライン**で渡し、題・作者を外す（二重盲検）。評価者ごとに JSON を
   `projects/<作品>/review/reports/vN/<評価者>.json` に保存する。

5. **JSON を確かめる。**
   ```
   <venv> engine/review.py validate --project projects/<作品> --version vN
   ```
   不正なら同じ評価者へ、エラーを添えて 3 回まで再依頼する。3 回で通らなければ
   `excluded` として理由を残す（黙って落とさない）。

6. **採点を記録して、表を見る。**
   ```
   <venv> engine/review.py record --project projects/<作品>
   <venv> engine/review.py table  --project projects/<作品>
   <venv> engine/review.py table  --project projects/<作品> --versions v1b,v4
   ```
   平均が 60 以下なら 7 へ。60 を超えたら、**それまでの最高版と比べて**採用を決める。
   **次元数が違う版を同じ平均で比べない。** 8 次元の旧版と 10 次元の新版は、
   `--versions` で並べるだけにし、比較は同じ評価者 id の集合で行う。

7. **直す。** 低い 2 次元（と 50 未満の次元）に絞る。高い次元は触らない。
   直したら vN+1 を書き、**新しい独立した評価者**で採り直す。同じ評価者に
   「直ったか」を聞かない（採点が甘くなる）。
   人物が弱い → キャラ表の `contradiction` / `humor` / `habits` と台詞。
   感情が弱い → 名指しを削り、間と反応で作る。

8. **視聴者の門を通す。** 評議会の点数が高くても、ここを通らなければ採用しない。
   [guide-viewer](../guide-viewer/SKILL.md) で、台本だけを渡した初見の読者 3 人と、
   説明の設計の評価者 1 人を立てる。`design.md` の「説明の鎖」から `facts.yaml` を
   作る。同じ事実を平文で書いた基準版も 3 人に読ませ、`engine/viewer.py record
   --baseline <基準>` で門を判定する（理解度のしきい値は基準の平均 − 10）。
   **文学評議会の平均に混ぜない。** 別の台帳（`review/viewers/<版>.yaml`）に残す。

9. **採用する。** 文学の平均が 60 を超え、**かつ視聴者の門を通った**版だけ。
   ```
   <venv> engine/review.py record --project projects/<作品> --adopted vN
   ```
   採用版を `projects/<作品>/台本.md` に写す。採用しなかった版も `review/drafts/` に残す。

10. **演技を付ける。** 採用本文を YAML にする前に
    [guide-acting](../guide-acting/SKILL.md) へ渡す。全 cue に
    `beat` / `emotion` / `face` / `speed` / `pause_before` / `volume` と、
    聞き手の `react`（`face` / `mark`）を置く。`acting.py audit` を通す。

11. **焼ける形へ起こす。** `script.yaml` / `video.yaml` / `chapters.yaml` を作る。
    起こし方は下の「YAML へ起こす」。最後に必ず:
    ```
    <venv> engine/scriptcheck.py --project projects/<作品>
    <venv> engine/acting.py audit --project projects/<作品>
    ```

12. **読みと BGM へ。** [guide-reading](../guide-reading/SKILL.md) →
    [guide-bgm](../guide-bgm/SKILL.md) → `engine/make.sh`。

## 説明の層と感情の層

**説明動画では、この二つを同じ調子で書かない。** 情感の断片は強いが、説明の断片は
意味を落とす。文学評議会は前者を高く評価するので、後者まで断片にすると、
評議会の平均だけが上がって、視聴者は何も持ち帰れない。

### 説明の層（事実・因果・数字）

- **1 cue = 1 命題。** 主語と述語を落とさない。「測る側が、ずれていた。」で止めず、
  「装置がずれていたので、鏡は設計と違う形に磨かれた。」まで書く。
- **読点は、文節の切れ目に打つ。一語ずつ区切らない。** 説明の cue では
  「鏡の前に置く、小さな装置だ。」と書く。「鏡の、前に、置く、小さな、装置だ。」は
  使わない。読点が多すぎると、声は息継ぎを繰り返し、視聴者は文の構造を追えなくなる。
  情感の cue でも、事実を運ぶ文は同じ規則で書く。
  `engine/scriptcheck.py` が、読点 3 つ以上・区切りの平均 4 字以下を警告する
  （`--strict` では失敗）。
- **事実の柱は、章ごとに一度は平文で言う。** 比喩と省略だけで済ませない。
- **数字には、分母と単位を同じ cue か隣の cue に置く。** 「99.8%」だけで終わらせない。
- **専門語は、初出で一言の定義を置く。** 「null corrector。鏡の形を、光で測る装置。」
- **指示語の受け手を、直前に置く。** 「それ」「その」だけで新しい対象を出さない。
- **因果は接続語で明示する。** 「だから」「その結果」「つまり」を惜しまない。
- **1 章に一度は、視聴者が答えられる問いと答えの組を置く。**
- **体言止め・読点止めは、説明の cue では使わない。** 感情の cue では使ってよい。

### 感情の層（beat・間・表情・反応）

- これまでどおり、感情を名指しせず、`beat` / `speed` / `pause_before` / `react` で作る。
- **断片でよい。** 「まだ、いい。」「……悪くない。」は、感情の cue として残す。
- **説明の cue を感情の調子に合わせない。** 平文で書いた事実の cue に、
  `beat` と間を付ければ、説明は説明のまま情感を持つ。

### 見分け方

その cue を消したとき、視聴者が**出来事・原因・数字のどれかを失う**なら説明の層。
**人物の感情の推移だけを失う**なら感情の層。前者は平文、後者は断片でよい。

## YAML へ起こす

- **1 cue = 1 文**（長くても息継ぎ 1 回）。`name` は `c001` から連番。
- **`……` だけの行は cue にしない。** 声を持たない行は音にならず、`build_voice.py` が
  落ちる。その間は次の cue の `pause_before` に畳む（0.6 秒の沈黙なら次の行へ +0.6）。
- `character` は `characters/<id>.character.yaml` / `cast.yaml` の id。固有名は書かない。
- `line` は**字幕に出したい文**。読みは `reading.yaml` が別に持つ（guide-reading）。
- **演技の欄**（guide-acting の出力）:
  `emotion` / `beat` / `face` / `speed` / `pause_before` / `volume` / `react`。
  `beat` は人物票のキーで、**顔はそこから解決される**（`export_timeline.py`）。
  `face` は動かしたい所だけ明示する（明示が優先）。
- `pause_before` / `speed` は、効かせたい所だけ。全部に同じ値を書くと演技が平坦になる。
- **字幕は 27 字以内。** 超える行は文の切れ目で割る。割れないなら文を短くする。
- `video.yaml` の `chapters` は章の頭の cue。`chapters.yaml` は同じ cue の配列
  （音のチャイム）。**両方を揃える。**
- `display` は、`line` と字幕を変えたい cue だけ。読みの段が無い作品では必須になる。

## 評価の読み方

- **平均だけを見ない。** 分散が大きい版は、評価者の見方が割れている。割れは弱点の在処。
- **`character-depth` と `character-role` は、人物の差が出ているかを見る。**
  台詞の量ではなく、欲と怖れの衝突、相手を動かす手、リスクを取る瞬間。
- **prose-style と anti-generic-story-filter は最後まで残りやすい。** 解説動画では、
  事例が等しい重みで並ぶと anti-generic が落ちる。章ごとに重さを変える。
- **評価者を替えても平均は ±3 点ほど動く。** 1 点の差で採否を決めない。
- **文学の平均と、視聴者の門は別の物差し。** 足さない・混ぜない・平均しない。
  文学が高いのに門が落ちる版は、**説明として失敗している**。逆も同じ。
- 評価 JSON の `caveats` / `excluded` は消さない。次の版の判断材料になる。

## A/B（旧版と新版を同じ物差しで）

1. 旧版の採用本文を `review/drafts/v1b.md` に写す。
2. v1b と新版を、**同じ時期に、同じ評価者 id の集合で、それぞれ独立の 10 本ずつ**評価する。
3. `review.py validate` → `record` → `table --versions v1b,v4`。
4. `review.py compare --before v1b --after v4` で、次元ごとの差を見る。
   評価者 id が違えば `compare` は失敗する（片方だけ使い回さない）。

## やらないこと

- 評価者に題・作者・採用予定を伝える。
- 平均を上げるために、評価者の弱点だけをなぞる（作品が評価に最適化される）。
- 60 を超えた最後の版を、無条件に採用する。**最高版を採る。**
- 8 次元の旧版と 10 次元の新版の平均を、そのまま比べる。
- **評議会の平均だけを根拠に採用する。** 視聴者の門（guide-viewer）を通す。
- **説明の因果を「余白」として隠す。** 主題は言わない。事実と因果は言う。
- **文学の点数を上げるために、事実の cue を断片にする。**
- Markdown から YAML への自動変換。文の切れ目と cue 名は意味判断なので、ここで行う。
- 演技を YAML 化の後に足す。感情の設計は台詞より先。

## 参照

- 往復の詳細・評価者の渡し方・版の残し方 → `references/loop.md`
- 設計 → [guide-design](../guide-design/SKILL.md)
- 人物 → [guide-cast](../guide-cast/SKILL.md)
- 演技 → [guide-acting](../guide-acting/SKILL.md)
