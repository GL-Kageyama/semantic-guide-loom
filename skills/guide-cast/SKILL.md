---
name: guide-cast
description: 人物の造形を、一人 1 ファイル（characters/<id>.character.yaml）に起こし、関係を persona.yaml に分ける。cast.yaml が画面の誰かを持つに対し、character.yaml は欲しいもの・怖いもの・矛盾・癖・笑い・話し方・感情の型を持つ。既存の採用台本から癖を測り（engine/persona.py analyze）、台本と演技へ人物票を渡す（brief）。設計とguide-scriptの間に立つ段。
argument-hint: 'キャスト名か作品の置き場。例: mirai-mirabo / projects/<作品>'
---

# guide-cast — 人物を、台本と表情に効く形で作る

**3 つのファイルを混ぜない。**

| ファイル | 持つもの | 例 |
| --- | --- | --- |
| `characters/<キャスト>.cast.yaml` | 画面の誰か（slot・表情シート・口・揺れ） | 絵の都合 |
| `characters/<id>.character.yaml` | 一人ぶんの人物造形（欲・怖れ・矛盾・癖・感情の型） | 言葉と演技の正本 |
| `characters/<キャスト>.persona.yaml` | 二人（以上）の関係（engine・rule・dynamics） | 掛け合いの型 |

**一人 1 ファイルにする理由。** 人物は作品をまたいで使う。作品ごとに変わるのは
台本の cue であって、その人が何を怖がるかではない。1 ファイルに複数人を詰めると、
作品の数だけ人物が分裂し、前の作品で作った造形が使えなくなる。

## 手順

1. **既にある台本から測る。** 採用版の `script.yaml` と `video.yaml` を読み、
   `engine/persona.py analyze --project <作品>` を走らせる。cue 数・平均字数・疑問文や
   百分率の率・文末の癖が出る。**印象ではなく、実際に書いた文から取る。**

2. **設計を読む。** `design.md` の「役割」と「最後に残す問い」を、人物の欲と怖れへ翻訳する。
   役割は「何をする人か」ではなく、**「何を守ろうとしている人か」**。

3. **一人 1 枚を書く。** `characters/<id>.character.yaml`。`id` は cast と
   `script.yaml` の `character` に一致させる。欄は `references/persona-sheet.md`。

   - `concept` … 一行。この人を一言で言うと。
   - `contradiction` … **一番大事な欄。** 欲しいものと怖いものが噛み合わない所。
     ここが台詞の衝突と、感情の型の源泉になる。
   - `habits` / `humor` … 台詞と間に出る癖。説明ではなく、動作で書く。
   - `speech` … `register` / `length` / `tempo` / `tics` / `avoids`。
     「常体」「3〜20字」のように、**判定できる言葉**で書く。
   - `emotions` … 6 つ以上（目安 8〜11）。キーは自由（`doubt` / `pride` / `shame` …）。
     各 beat に `face`（cast の expressions に実在する名前）、`voice`（SAL の感情）、
     `speed` / `volume` / `delivery` / `intensity`、`tell`（台詞に漏れるもの）、
     `body`（身体の動き）、`withhold`（名指ししないこと）。
   - `samples` … 作品の筋ではない短い行。声と間の見本。`beat` は `emotions` のキー。

4. **関係を書く。** `characters/<キャスト>.persona.yaml` に `pair` だけを置く。
   `engine`（掛け合いを動かす仕組み）、`rule`（守るべき一行）、
   `dynamics`（相手の組ごとの engine / rule / escalation）。
   **人物の中身はここへ戻さない。** 旧形式の `characters[]` は読めるが、新規は書かない。

5. **突き合わせる。**
   ```
   <venv> engine/persona.py check --cast <キャスト>
   ```
   cast の id ごとに 1 枚あるか、`emotions` が 6 つ以上か、`face` が cast に実在するか、
   `voice` / `speed` / `volume` / `delivery` / `intensity` が SAL の語彙か、
   `samples` の beat が実在するか、`relationship.to` が相手を指すかを見る。

6. **人物票を渡す。**
   ```
   <venv> engine/persona.py brief --cast <キャスト>
   <venv> engine/persona.py brief --cast <キャスト> --character <id>
   ```
   出力を guide-script と guide-acting の冒頭に貼る。**台本を書く間も、演技を付ける間も、
   この票が人物の正本。**

## 決めること

- **register（常体／丁寧／混在）** … 二人の関係が最初に出る。
- **一文の長さ** … 字幕の 27 字と、声の息継ぎに直結する。
- **tics（繰り返してよい言い回し）** … 3〜5 個。増やすと記号になる。
- **avoids（この人物に言わせないこと）** … 講義口調、感情の名指し、断定など。
- **emotions の幅** … 同じ表情に寄せすぎない。cast の 8 マスのうち、まばたきを除いた
  6 つを、最低 5 つ使う。使わない表情があるなら、その感情をこの人が持たない理由を考える。
- **arc（作品を通した変化）** … 解説動画でも、最後に少しだけ変わる。

## やらないこと

- `character.yaml` に絵の欄（slot / sheet / scale / mouth_offset）を書く。それは cast。
- `character.yaml` に作品の固有名詞・事件・章番号を書く。それは作品（design / script）。
- コードに固有名を書く。名前は `characters/` と `script.yaml` にだけ出る。
- まばたきの表情（`blink_*`）を `face` に指定する。この版ではまばたきをしない。
- 設定を作品ごとに固定する。人物は作品をまたぐが、**演技は作品ごとに見直す**。

## 次へ

- 演技の設計と付与 → [guide-acting](../guide-acting/SKILL.md)
- 台本の生成と評価 → [guide-script](../guide-script/SKILL.md)
- 読みの用意 → [guide-reading](../guide-reading/SKILL.md)
