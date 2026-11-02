---
name: guide-acting
description: 台本の各行に演技を付ける。章ごとの感情の弧を先に設計し（review/acting/plan.md）、採用後の全 cue に beat・emotion・face・speed・pause_before・volume と、聞き手の反応（react の face・mark）を置く。engine/acting.py で参照切れ・網羅・単調さを測り、版ごとの計測を review/acting/<版>.yaml に残す。guide-script と guide-reading の間に立つ段。
argument-hint: '作品の置き場。例: projects/<作品>'
---

# guide-acting — 感情を、台本・声・顔・身体・反応に載せる

演技は後付けの装飾ではない。**台詞を書く前に、誰が何を漏らし、何を隠すかを決める。**
その設計が台詞の選び方を変え、最後に cue の欄へ落ちる。

**感情を名指ししない。** 「悲しい」「嬉しい」と書く代わりに、間・速度・表情・身体・
聞き手の反応で作る。SAL の実測では、声が動くのは `speed` と `pause_before` が主で、
`emotion` は粗い切替、`volume` はミックス側。**表情・身体・反応が主役。**

## 2 つの局面

### 書く前 — 感情の弧を設計する

`review/acting/plan.md` に置く。guide-script はこれを読んでから台詞を書く。

```markdown
# 感情の弧

## 章ごと
| 章 | 欲求 | 障害 | 転換 | 落とし所 |
| --- | --- | --- | --- | --- |
| 序章 | 現在地を知りたい | 数字の分母が言えない | 問いを立てる | まだ安心しない |

## 人物ごと
| 人物 | 漏らす感情 | 隠す感情 | 漏れ方（動作・文末） |
| --- | --- | --- | --- |
| … | 驚き | 不安 | 数字を二度言う |

## 山場と沈黙
- 山場: どの cue。何を言わずに置くか
- 沈黙: どの cue の前に、何秒

## 反応の置き所
- 誰が、誰のどの cue に、顔だけ／記号つきで反応するか（記号は全体で 8〜15 か所）
```

**反応の顔は、話し手の感情の写しではない。** その人物がその話をどう受けるかで決める。
疑う人は疑い、当てたい機体は外れの予感に怯える。

### 採用後 — cue に演技を付ける

`script.yaml` の各 cue に、次を置く。**`script.yaml` の形の正本は SAL の
`schemas/scene.schema.json`**。SAL は追加キーを許すので、演技の欄はそこに載る。

```yaml
- name: c009
  character: mirabo
  line: "99.8%です。"
  emotion: confidence       # 声（SAL の 11 感情）
  beat: pride               # 人物票の感情キー（演技の意図）
  face: excited             # 省略可。明示すると beat より優先される
  speed: fast
  pause_before: 0.3
  volume: normal
  react:                    # 聞き手の反応（この cue の間）
    mirai: {beat: doubt, mark: "？"}
```

- **`beat` が演技の正本。** 顔は人物票の `emotions.<beat>.face` から
  `export_timeline.py` が解決する。timeline には解決済みの `face` が入るので、
  絵の側は同じ時刻に同じ顔を出す（決定的）。
- **`face` は省略してよい。** 動かしたい所だけ、cast の expressions に実在する
  名前で明示する（明示が優先）。まばたき（`blink_*`）は使わない。
- **`react.<id>.beat` で顔が決まる。** 明示 `react.<id>.face` も同じ規則。
- **記号だけの反応もよい。** `react: {mirai: {mark: "？"}}` は顔を変えずに記号だけ。
  顔だけの反応もよい。両方無い反応はエラー。
- **記号は 3 文字まで。** `！` `？` `……` `！？` など。全体で 8〜15 か所、山場だけ。
  同じ人物に続けて置かない。
- **`pause_before` は 0.15〜2.2 秒に広げる。** 全部に書かない。沈黙を作る所だけ。
- **`speed` は 4 語以上。** `very_slow` / `slow` / `natural` / `fast` / `very_fast`。
  同じ速度を長く続けない（最長連続が全体の 25% 未満）。

## 声の欄の効き方（SAL の実測）

| 欄 | 効き方 |
| --- | --- |
| `speed` | 最も確実。5 語。間の取り方も変わる |
| `pause_before` | 確実。呼吸と沈黙を作る |
| `emotion` | 粗い切替。隣り合う感情は差が出にくい |
| `volume` | ミックス側で効く。強弱は BGM との関係で決まる |
| `delivery` | `cold` / `flat` / `aggressive` / `desperate` の 4 語だけ効く |
| `pitch` / `intonation` / `intensity` | 音はほとんど動かない。演技の意図としてだけ書く |

**声だけで感情を作らない。** 顔・身体・反応・間が先。声はその裏づけ。

## 検査と計測

```
<venv> engine/scriptcheck.py --project projects/<作品>
<venv> engine/acting.py audit --project projects/<作品>
<venv> engine/acting.py audit --project projects/<作品> --strict   # 警告も失敗
<venv> engine/acting.py report --project projects/<作品> \
    --out projects/<作品>/review/acting/v4.yaml --version v4
<venv> engine/acting.py compare \
    --before projects/<作品>/review/acting/v1.yaml \
    --after  projects/<作品>/review/acting/v4.yaml
```

`audit` が見るもの:

- 参照切れ（emotion / speed / volume / delivery / intensity が SAL の語彙か、
  face が cast に実在するか、beat が人物票にあるか、react の相手が cast に居るか）
- beat と face の網羅率（目標 90%）
- 人物ごとの表情の種類（目標 5 種類以上）
- 聞き手の反応（顔）の率（目標 60%）、記号の数（目標 8〜15）と連続
- 速度の種類（目標 4 語以上）と最長連続（目標 25% 未満）
- `pause_before` の広がり（0.15〜2.2 秒）

**計測は `review/acting/<版>.yaml` に置く。`review/reports/` には置かない**
（`review.py` が評価者の JSON と数えてしまう）。旧版を測るときは
`--script <旧 script.yaml>` を使う。置き換える前の証拠を残せる。

`make.sh` は焼く前に `scriptcheck.py` と `acting.py audit` を非 strict で走らせる。
演技の欄が無い古い作品も止めない。`STRICT=1` のときだけ警告で止まる。

## 完了の目安

- 全 cue の 90% 以上に `beat` と `face`（明示）。
- 各人物が 5 種類以上の表情。
- 聞き手の反応（顔）が、聞き手のいる cue の 60% 以上。記号は 8〜15 か所。
- 速度が 4 語以上、`pause_before` が 0.15〜2.2 秒に広がる。
- 同じ速度の最長連続が全体の 25% 未満。
- **同じ 6 場面の旧版 / 新版のフレームを並べて、表情・反応・記号の差が目で分かる。**

数値は足切りではない。**足りない所を、人物の矛盾へ戻って直す**ための測り。

## やらないこと

- 感情を台詞で名指しする（「悲しい」「嬉しい」）。
- `face` を全 cue に書き写す（`beat` から解決される。明示は動かす所だけ）。
- まばたきを入れる。
- 記号を全 cue に置く。紙吹雪・ランダム・画面の賑やかしは使わない。
- 声の欄だけで感情を作る。`pitch` / `intonation` に頼る。
- 評価の言葉をそのまま演技にする（「もっと余白を」は cue の欄ではない）。

## 参照

- 欄の一覧と書き方 → `references/acting-sheet.md`
- 人物票 → [guide-cast](../guide-cast/SKILL.md)
- 台本と評議会 → [guide-script](../guide-script/SKILL.md)
- 読み → [guide-reading](../guide-reading/SKILL.md)
