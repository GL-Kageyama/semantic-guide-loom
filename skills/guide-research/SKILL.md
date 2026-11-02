---
name: guide-research
description: 解説動画の題材を、設計より先に調べる。公式・一次資料を当たり、検索語・出典・抜き書き・検証済みの事実を projects/<作品>/research/ に残す。設計・台本・詳細カードは facts.yaml の id を引き、焼く時はネットを見ない。調査から作る最初の段。
argument-hint: '題材か作品の置き場。例: ハッブル望遠鏡の鏡 / projects/<作品>'
---

# guide-research — 調査から作る

解説動画は、**言ってよい事実**が先に決まっていないと、台本もカードも雰囲気で埋まる。
この段は、題材の約束を一文で置き、公式・一次資料を当たり、**作品の隣に台帳を残す**。
設計（guide-design）・台本（guide-script）・詳細カードは、その台帳の事実 ID を引く。

**焼く時は検索しない。** `engine/make.sh` は台帳を読むだけで、ネットを見ない。

## 手順

1. **約束と問いを一文ずつで置く。** 誰が、何を知らずに来て、見終わった後に何を
   持ち帰るのか。題材の中心にある問いを、まだ答えずに書く。
2. **公式・一次資料を先に当たる。** NASA / ESA / 研究機関のページ、論文、
   当時の報道、規格。二次的なまとめは、公式が届かない箇所だけに使う。
   検索語と当たった資料は `queries.md` に残す。
3. **出典ごとに `notes/<source-id>.md` を書く。** 短い引用・頁・単位・分母を残し、
   全文を写さない。引用できないときは「要旨（引用ではなく要約）」と明記する。
4. **`sources.yaml` に出典を並べる。** `id` / `title` / `kind` / `url` か `path` /
   `accessed` / `confidence`。`kind` は `official` / `paper` / `reference` / `news` /
   `in-work`。`accessed` は `YYYY-MM-DD`（**引用符で囲む**。YAML が日付型に変えるため）。
5. **`facts.yaml` に「映像で言ってよい事実」を書く。** 1 fact = 1 つの主張。
   `statement` / `sources`（1 つ以上）/ `confidence` / `used_by`（任意）。
   事実と解釈を分ける。作品内の予測（例: 99.8% / 97%）は `kind: in-work` の出典に置き、
   外部の数字と混ぜない。**分母のない百分率を fact にしない。**
6. **衝突したら公式・新しい資料を優先する。** 古い値を採らなかった場合も、
   **訂正を `queries.md` に残す**（前の値 / 直した値 / 出典）。同じ調べ直しを繰り返さない。
7. `<venv> engine/scriptcheck.py --project projects/<作品> --strict` で、fact の
   参照切れと `confidence: low` のカードを見る。

## 置き場

```
projects/<作品>/research/
  README.md          この作品の調査の目的・範囲・更新の仕方
  queries.md         検索語、当たった資料、分かったこと・分からなかったこと、訂正
  sources.yaml       出典
  notes/<source-id>.md  出典ごとの抜き書き
  facts.yaml         映像に使う事実
```

`research/` は**作品の入力**で、`build/` のような派生ではない。テキストなので Git に入れる
（LFS の対象外）。

## 台帳の形

`schemas/research.schema.json` が `sources.yaml` と `facts.yaml` の形を持つ。
`tools/check_layout.py` が実物に通す。

```yaml
# sources.yaml
sources:
  - id: nasa-optics
    title: Hubble Observatory — Optics
    kind: official
    url: https://science.nasa.gov/mission/hubble/observatory/design/optics/
    accessed: "2026-11-03"
    confidence: high

# facts.yaml
facts:
  - id: mirror-spec
    statement: 主鏡は直径2.4m、828kg、ULEガラス。表面の凹凸は1µm未満。
    sources: [nasa-optics]
    confidence: high
    used_by: [c006]
```

## カードとのつなぎ

`video.yaml` の詳細カードは `fact` を持つ。

```yaml
details:
  - cue: c006
    head: 主鏡
    lines:
      - 直径 2.4メートル
      - 重さ 828キログラム
      - 素材は ULE ガラス
      - 表面の凹凸は 1µm 未満
    fact: mirror-spec
```

- カードの文は **fact の範囲を出ない**。fact に無い数字・日付・固有名を足さない。
- カードを足すために新しい主張が要るなら、**先に `sources.yaml` と `facts.yaml` を足す**。
- `fact` を付けないカードは警告になる。新しい作品では必ず付ける。

## 気をつけること

- **公式を先に。** Wikipedia やまとめ記事だけで fact を作らない。
- **単位と分母を残す。** 「97%」は何を何で割ったか。「1.3mm」は何と何の差か。
- **別の量を混ぜない。** 例: 1.3mm（field lens のずれ）と 2.2µm（鏡の縁の平らさ）は別。
- **古い値を消さない。** 訂正は `queries.md` に残す。読む人が、なぜ直したかを辿れる。
- **焼く時に検索しない。** 調査は焼く前の段だけ。`make.sh` に検索を足さない。
- **`review/facts.md` は台本の門の記録。** 詳細カードの正本は `research/facts.yaml`。
