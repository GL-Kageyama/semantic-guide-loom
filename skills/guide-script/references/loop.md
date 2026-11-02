# 生成と評価の往復

## 置き場

```
projects/<作品>/
  design.md
  review/
    drafts/v1.md v2.md …        評価に渡した本文（制作メモを入れない）
    reports/v1/<評価者>.json    評価者の返答をそのまま
    scores.yaml                 engine/review.py record が書く
    facts.md                    事実確認
    acting/plan.md              感情の弧（guide-acting が台詞の前に作る）
    acting/vN.yaml              版ごとの演技の計測（reports/ には置かない）
  台本.md                       採用版
  script.yaml video.yaml chapters.yaml
```

## 評議会への渡し方

評価者を**別々の subagent** として起動する。同じ会話でまとめて聞かない（独立性が壊れる）。

**次元の数はキャストで決まる。**

| 作品 | 次元 | 評価者 |
| --- | ---: | --- |
| キャストが居る（掛け合い） | 10 | `hook / plot-architecture / reader-experience / prose-style / admiration / anti-generic-story-filter / theme-resonance / emotional-power / character-depth / character-role` |
| 語りだけ | 8 | 上の 8 つ（character-* を除く） |

各 subagent へ渡すもの:

- 本文（題・作者を外したもの）
- `content_type: "text"`、`domain`（解説なら `short-story` か `genre-fiction`）
- 出力は JSON のみ。フィールドの定義は評価者側にあるので、**schema のパスを渡さない**
  （読もうとして止まることがある）
- 自由記述は日本語

評価者名は `hook-ja` のように言語接尾辞を付ける。plugin として入っている場合は
`novel-council-layer:hook-ja`。

## JSON の検証

```
<venv> engine/review.py validate --project projects/<作品> --version vN
```

内部で `novel-council-layer/utils/validate_output.py --json` を呼ぶ。
`primary_score` は 0〜100 の整数。欠けたら評価者へ再依頼する。

## 改稿の単位

| 低い次元 | まず見る所 |
| --- | --- |
| hook | 冒頭で立てた約束が、最後まで引いているか。章の境目で切れていないか |
| plot-architecture | 情報の開示順。答えが次の問いを内側から開いているか |
| reader-experience | 1 行の長さ、間、テンポ。同じ調子が続いていないか |
| prose-style | 読点の刻み、文末の単調さ、同じ比喩の繰り返し |
| admiration | 予測を超えて、しかも必然に感じる「おおっ」があるか |
| anti-generic-story-filter | 事例が等しい重みで並んでいないか。どこにでもある説明になっていないか |
| theme-resonance | 題が最後の問いへ届いているか。説明だけで終わっていないか |
| emotional-power | 感情を名指ししていないか。抑制のある場面があるか |
| character-depth | 欲と怖れが噛み合っていないか。人物が設定の口になっていないか |
| character-role | 人物が自分から動いているか。リスクを取り、相手を動かしているか |

**一度に直すのは 2 次元まで。** 全部を直すと、何が効いたか分からなくなる。

## 人物と演技の往復

- **台詞より先に `review/acting/plan.md`。** 章ごとの欲求 → 障害 → 転換 → 落とし所、
  人物ごとの「漏らす／隠す」、山場と沈黙、反応の置き所。
- 採用本文を YAML にする前に、guide-acting で全 cue に演技を付ける。
  `beat` / `emotion` / `face` / `speed` / `pause_before` / `volume` と `react`。
- 演技が弱いときは、記号を増やさない。**人物の `contradiction` へ戻る。**
- 版ごとの計測は `review/acting/vN.yaml`。`review/reports/` に置くと、
  `review.py` が評価者の JSON と数えて平均を壊す。

## 版を残す

- `review/drafts/vN.md` は、評価に渡したそのまま。後から直さない。
- `review/reports/vN/` は評価者の返答。失敗した JSON も消さず、`excluded` の理由を残す。
- `review/scores.yaml` は `record` の出力。手で平均を書かない。
- 採用版は `台本.md` に写し、`review/README.md` に「どの版を、なぜ採ったか」を一行で残す。

## A/B の作法

- 旧版（`v1b`）と新版（`v4`）を、**同じ時期に、同じ評価者 id の集合で、
  それぞれ独立の 10 本ずつ**評価する。
- `review.py compare --before v1b --after v4` は、評価者 id が違えば失敗する。
  片方だけ評価者を使い回さない。
- **8 次元の旧版と 10 次元の新版の平均を、そのまま比べない。**
  `table --versions v1b,v4` で並べ、比較は同じ id の集合で行う。
  共通 8 次元の平均は `compare` が出す。

## よくある失敗

- **評価者に前の版を見せる。** 差分の説明を始め、独立した採点にならない。
- **平均だけを追う。** 分散の大きい版の方が、読む人には刺さることがある。
- **60 を超えたら即採用。** 最高版でないことがある。表を見てから決める。
- **評価の言葉をそのまま台詞にする。** 「もっと余白を」は台本の一文ではない。
- **演技を後付けする。** 記号と表情だけ足しても、人物が動いていなければ平坦なまま。
