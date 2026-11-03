# `research/` — 調査の台帳（作品が持つ。任意）

**焼く前の段。** 題材が決まったら、設計より先に検索・取得・検証を行い、事実を台帳に
残す。`make.sh` はここを読むだけで、**検索も取得もしない**。

```
research/
  README.md       この作品の調査の目的・範囲・更新の仕方
  queries.md      検索語、当たった資料、分かったこと・分からなかったこと、訂正
  sources.yaml    出典（id / title / kind / url or path / accessed / confidence）
  notes/<id>.md   出典ごとの抜き書き（短い引用・頁・単位・分母）
  facts.yaml      映像に使う事実（id / statement / sources / confidence / used_by）
```

## `sources.yaml`

`kind` は `official` / `paper` / `reference` / `news` / `in-work`。`in-work` は
作品内の予測・演出（例: 99.8% は記録ではなく作品の値）。`url` か `path` の
どちらかを持ち、`accessed` は `YYYY-MM-DD`（**引用符で囲む**）。

## `facts.yaml`

1 fact = 1 主張。`sources` は 1 つ以上で `sources.yaml` の id を指す。
`confidence` は `high` / `medium` / `low`。

**`video.yaml` の `details[].fact`** が fact の id を指す。カードの文は fact の範囲を
出ない。`confidence: low` の fact をカードに使うと `scriptcheck.py` が警告する。

## 検査

形は `schemas/research.schema.json`。**参照の検査は `scriptcheck.py`。**

```bash
engine/scriptcheck.py --project projects/<作品>
```

- `details` があるのに `research/` が無い → 警告
- 未知の fact → エラー
- fact の `sources` が解決しない → エラー

## 置き場

台帳は**入力**（テキスト）なので Git に入れる。`build/` へ移さない
（[placement.md](placement.md)）。

**新しい事実は、先に台帳へ足す。** 焼く時に検索しない——同じ台本から同じ絵が出る
ことが、このリポジトリの前提である。
