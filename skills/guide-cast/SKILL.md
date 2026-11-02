---
name: guide-cast
description: キャラクターの「言葉の設定」を persona.yaml に起こし、台本に活かす。cast.yaml が画面の誰かを持つに対し、persona.yaml は話し方・欲しいもの・怖いもの・手を持つ。既存の採用台本から癖を測り（engine/persona.py analyze）、台本を書く側へ人物票を渡す（brief）。設計（design.md）とguide-scriptの間に立つ段。
argument-hint: 'キャスト名か作品の置き場。例: mirai-mirabo / projects/<作品>'
---

# guide-cast — キャラ設定を、台本の言葉に変える

**cast.yaml は「画面の誰か」。persona.yaml は「どう話すか」。** 境界を混ぜない。
絵の都合（立ち位置・表情シート・口の形）は cast が持ち、言葉の癖は persona が持つ。

出力は `characters/<キャスト>.persona.yaml`。台本を書くたびに `engine/persona.py brief`
で短い人物票にし、guide-script のプロンプトへ貼る。

## 手順

1. **既にある台本から測る。** 採用版の `script.yaml` と `video.yaml` を読み、
   `engine/persona.py analyze --project <作品>` を走らせる。cue 数・平均字数・疑問文や
   百分率の率・文末の癖が出る。**印象ではなく、実際に書いた文から取る。**
2. **設計を読む。** `design.md` の「二人の役割」と「最後に残す問い」を、言葉の設定へ翻訳する。
3. **`characters/<キャスト>.persona.yaml` を書く。** 欄は `references/persona-sheet.md`。
   一人につき、`role` / `wants` / `fears` / `stance` / `speech` / `moves` / `arc`。
   `speech` は「常体」「8〜25字」のように、**判定できる言葉**で書く。
4. **cast と突き合わせる。** `engine/persona.py check --cast <キャスト>` で id と必須欄を見る。
5. **人物票を渡す。** `engine/persona.py brief --cast <キャスト>` の出力を、guide-script の
   冒頭に貼る。台本を書く間、この票が唯一の人物の正本になる。

## 決めること

- **register（常体／丁寧／混在）** … 二人の関係が最初に出る。
- **一文の長さ** … 字幕の 27 字と、声の息継ぎに直結する。
- **tics（繰り返してよい言い回し）** … 3〜5 個。増やすと記号になる。
- **avoids（この人物に言わせないこと）** … 講義口調、感情の名指し、断定など。
- **moves（場面で取る手）** … 具体例を出す、質問を返す、数字で現在地を示す。
- **arc（作品を通した変化）** … 解説動画でも、最後に少しだけ変わる。

## やらないこと

- persona に絵の欄（slot / sheet / scale / mouth_offset）を書く。それは cast。
- コードに固有名を書く。名前は `characters/` と `script.yaml` にだけ出る。
- 設定を作品ごとに固定する。persona は**その作品の声の仮説**。作品が変われば見直す。

## 次へ

- 台本の生成と評価 → [guide-script](../guide-script/SKILL.md)
- 読みの用意 → [guide-reading](../guide-reading/SKILL.md)
