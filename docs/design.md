# `design.md` — 設計（作品が持つ。任意）

台本を書く前の設計。題材・視聴者・約束・事実の柱・**説明の鎖**・章・二人の役割・
最後に残す問い。**形は決めない**（Markdown）。`guide-design` の
`references/design-sheet.md` が型。

## 説明の鎖

視聴者が台本だけで復元できる問い（3〜7 個）と、それを平文で言う場所の対応を持つ。
**主題（約束）はここに入れない。** 主題は言わない。事実と因果は言う。

この表が `review/viewers/<版>/facts.yaml` の元になる。事実の値は
`research/facts.yaml` と揃える（設計・門・カードで別の数を言わない）。

## 順番

```
research/（事実） → design.md（設計） → script.yaml / video.yaml（台本） → 評価
```

**調査が先。** 設計より先に、検索・取得・検証を行い、事実を台帳に残す
（[research.md](research.md)）。焼く時にネットを見ない。

## 台本との関係

- 章・事実の柱・説明の鎖は `video.yaml` の `chapters` と `details` に降りる
- 二人の役割は `characters/*.persona.yaml` に降りる（[characters.md](characters.md)）
- 説明の鎖は `review/viewers/` の問いになる（[review.md](review.md)）

`design.md` は**任意**。無ければ台本から直接焼ける。
