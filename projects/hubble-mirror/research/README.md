# 調査 — ハッブルの鏡

詳細カードに載せる事実を、台本の外から取り直した台帳。**台本（`script.yaml` / `台本.md`）と
声は温存**し、カードの材料だけをここで用意する。

## 範囲

- 打ち上げと軌道
- 主鏡の仕様と、最初の像
- 鏡の不具合（球面収差・null corrector・1.3mm）
- 修理（STS-61・COSTAR・WFPC2）
- ハッブル・ディープ・フィールド

## 正本

- **`facts.yaml`** — 映像で言ってよい事実。1 fact = 1 つの主張。
  `details[].fact` はこの id を引く。カードの文は fact の範囲を出ない。
- **`sources.yaml`** — 出典。`facts.yaml` の `sources` はこの id を引く。
- **`notes/<source-id>.md`** — 出典ごとの抜き書き（要旨・単位・分母）。
- **`queries.md`** — 検索語と、古い値の訂正。

`review/facts.md` は **v12 台本の門の記録**で、カードの正本ではない。

## 更新の仕方

1. 新しい主張は、先に `sources.yaml` と `notes/` を足す。
2. `facts.yaml` に 1 fact を足す。事実と解釈を分ける。作品内の予測は `kind: in-work`。
3. `video.yaml` の `details[].fact` を合わせる。
4. `python3 engine/scriptcheck.py projects/hubble-mirror` で参照切れを見る。

**焼く時に検索しない。** `engine/make.sh` はこの台帳を読むだけで、ネットを見ない。
