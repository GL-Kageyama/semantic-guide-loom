# `review/` — 二つの台帳（混ぜない）

台本の採否は、**別々の物差し**を両方通す。平均も足さない。

| 台帳 | 何を見るか | 道具 | 合格 |
| --- | --- | --- | --- |
| `review/reports/<版>/` | 文学評議会の 10 次元（物語・人物・情感） | `engine/review.py` | 平均 60 超 |
| `review/viewers/<版>/` | 初見の復元テスト（3 人）と説明の評価（1 人） | `engine/viewer.py` | 理解度は平文の基準 − 10 以上、各事実が 2/3 以上、説明 75 以上 |

```
review/viewers/<版>/
  facts.yaml       視聴者が答えるべき問い（id / question / answer）
  r1.json r2.json r3.json   初見の読者の返答（schemas/viewer.schema.json）
  explanation.json 説明の設計の評価
review/viewers/<版>.yaml   集計と門の判定（engine/viewer.py record が書く）
review/viewers/<基準>/plain.md   同じ事実を平文で書いた基準版
review/viewers/<基準>.yaml       基準の理解度（engine/viewer.py baseline が書く）
```

- **文学評議会は、説明の明瞭さを測らない。** 10 次元は物語としての強さを見る。
  断片・省略・余白が高得点になりうるので、解説動画には別の門が要る。
- **理解度の絶対値 75 は、平文の解説のための数字。** 掛け合いと感情の層を持つ
  台本は、同じ事実でも自己申告の理解度が下がる。同じ事実を平文で書いた基準版を
  同じ 3 人に読ませ、**基準の平均 − 10 点**を掛け合い版のしきい値にする。
  基準は台本より先に、`facts.yaml` と `design.md` から書く。事実の復元（2/3）と
  説明の評価（75）は基準でも変えない。
- **`review/reports/` に視聴者の JSON を置かない。** `review.py` が全部評価者として
  数え、文学の平均が壊れる。置き場を分ける。
- 読者には台本だけを渡す。`design.md`・人物票・前の評価を見せない。

## 次元の数

キャストの居る作品は **10 次元**（既存 8 + `character-depth` + `character-role`）、
語りだけなら 8 次元。**次元数が違う平均を混ぜない。**

## 演技の計測は別に置く

`review/acting/` は感情の弧（`plan.md`）と版ごとの計測（`vN.yaml`）。`review.py` は
`review/reports/` の `*.json` を全部評価者として数えるので、YAML の計測を混ぜると
平均が壊れる（[acting.md](acting.md)）。

## 道具

```bash
engine/review.py table    --project projects/<作品>                 # 版ごとの平均と採否
engine/review.py record   --project projects/<作品> --adopted v4    # review/scores.yaml
engine/review.py compare  --project projects/<作品> --before v3 --after v4
engine/viewer.py baseline --project projects/<作品> --version plain  # 平文の基準
engine/viewer.py record   --project projects/<作品> --version v4     # 門の判定
engine/viewer.py table    --project projects/<作品>
```

版ごとに `review/drafts/vN.md`・`review/reports/vN/*.json`・`review/viewers/vN/` を残す。
