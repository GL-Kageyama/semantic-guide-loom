---
name: guide-design
description: 台本の設計を、本文より先に作る。題材から design.md（視聴者・約束・事実の柱・章・二人の役割）を書き、評議会の plot モードで平均 60 を超えてから guide-cast / guide-script へ渡す。解説動画の「何を、どの順で、どこへ着地させるか」を決める段。
argument-hint: '題材か作品の置き場。例: 新入社員向けの経費精算 / projects/<作品>'
---

# guide-design — 台本の設計を、まず作る

本文を書く前に、**何を約束し、どの順で開き、どこへ着地させるか**を一枚に固定する。
設計が曖昧なまま台本を書くと、評価のたびに直す場所が変わり、往復が効かない。

出力は `projects/<作品>/design.md` 一枚。**台本ではない。** 文の運びは guide-script が書く。

## 手順

1. **題材と視聴者を一文ずつで言う。** 誰が、何を知らずに来て、見終わった後に何を
   持ち帰るのか。ここが曖昧なら、まだ書き始めない。
2. `references/design-sheet.md` の型で `design.md` を書く。章は「情報の順番」ではなく
   **問いの順番**で並べる。各章に「この章が開く問い」と「どこへ落ちるか」を書く。
3. **事実の柱を分ける。** 日付・固有名・数値・引用は、出典と確度を添えて列挙する。
   演出で足す比喩・場面・会話は、事実の柱と混ぜない。確認は `research-verify` の
   手順で行い、結果を `projects/<作品>/review/facts.md` に残す。
4. **二人の役割を決める。** 誰が問い、誰が予測し、誰が具体で崩すか。名前はここでは
   `characters/<キャスト>.cast.yaml` の id で書き、固有名は書かない。
5. **設計を評議会に掛ける。** `story-council` の plot モード（本文ではなく構想を評価）で、
   `hook / plot-architecture / theme-resonance / emotional-power / admiration /
   anti-generic-story-filter / world-building / character-role` の 8 体に渡す。
   `primary_score` の平均が **60 を超える**まで、章の順・問い・落とし所を直す。
   レポートは `projects/<作品>/review/design/<版>/` に置く。
6. 通ったら `guide-cast` へ。人物の言葉の設定を作ってから、`guide-script` で本文を書く。

## 設計で決めて、台本で決めないこと

- **約束**（見終わった後に何が変わるか）
- **章の数と順序**、各章の問いと落とし所
- **事実の柱**と、演出で足す部分の境界
- **二人の役割**（誰が疑い、誰が予測し、誰が崩すか）
- **最後に開いたまま残す問い**（解説動画でも、閉じ切らない方が強いことがある）

文の長さ・語尾・間・表情は、台本と人物の設定（`persona.yaml`）が決める。

## やらないこと

- 本文（台詞）を書く。それは guide-script。
- 型（template）や配色を決める。それは映像の側。
- 事実を雰囲気で埋める。確度の低いものは「報道ベース」「未確認」と書く。

## 次へ

- 人物の言葉の設定 → [guide-cast](../guide-cast/SKILL.md)
- 台本の生成と評価 → [guide-script](../guide-script/SKILL.md)
