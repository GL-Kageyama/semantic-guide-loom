# 演技の欄と、付け方

`script.yaml` の cue に載る演技の欄。形の正本は SAL の
`semantic-audio-loom/schemas/scene.schema.json`（追加キーを許す）。ここは意味と使い方。

## 話し手の欄

| 欄 | 型 | 何を決めるか | 目安 |
| --- | --- | --- | --- |
| `emotion` | SAL の 11 感情 | 声の粗い切替 | 全 cue の 90% |
| `beat` | 人物票のキー | 演技の正本。顔はここから解決 | 全 cue の 90% |
| `face` | cast の表情名 | 画面の顔（省略可・明示が優先） | 動かす所だけ |
| `speed` | `very_slow` / `slow` / `natural` / `fast` / `very_fast` | 話す速さ | 4 語以上 |
| `pause_before` | 秒（数値） | この cue の前の沈黙 | 0.15〜2.2 秒に広げる |
| `volume` | `whisper` / `quiet` / `normal` / `loud` / `shout` | ミックス側の強弱 | 山場だけ |
| `delivery` | SAL の 12 語 | 効くのは 4 語だけ | 必要な所だけ |
| `intensity` | SAL の 5 語 | 意図。音は動きにくい | 任意 |

`beat` は人物票の `emotions` のキー。**顔は `beat` から解決される**
（`export_timeline.py`）。`face` を書くのは、beat の既定から外したい時だけ。

## 聞き手の反応

```yaml
react:
  <相手の id>:
    face: <cast の表情名>     # 顔を変える（省略可）
    mark: "？"                # 記号（省略可、3 文字まで）
    beat: <人物票のキー>      # 顔はここから解決される（face は省略可）
```

- **顔と記号は独立して省略できる。** 記号だけ、顔だけ、両方。
- 両方無い反応はエラー。
- `face` は、その人物がその話を**どう受けるか**。話し手の感情の写しではない。
- `beat` だけで顔が決まる。`face` を省いてよい。
- 記号は全体で 8〜15 か所。山場だけ。同じ人物に続けて置かない。

### 画面での出方

- **顔**: 反応を置いた cue の `start` から、その人が次に話す cue の `start` まで保つ。
  同じ時刻に自分の発話が始まるなら、発話が勝つ。
- **記号**: `cue.start + lead`（型の `acting.reaction.lead`、既定 0.2 秒）から、
  `pop + hold + fade` の間だけ出る。自分の次の発話が始まったら、そこで消える。
- **身体**: `cast.yaml` の `motion_gain`（表情 → 倍率）が、**解決済みの face があるコマ**に
  掛かる。悲しみは小さく、驚きは大きく。未記載は 1.0。
- まばたきはしない。

## 付ける順番

1. **章ごとの弧を決める**（`review/acting/plan.md`）。欲求 → 障害 → 転換 → 落とし所。
2. **人物ごとの「漏らす／隠す」を決める。** 漏れ方は動作と文末に置く。
3. **山場を 1〜2 か所決める。** そこに記号と長い間を置く。他は静かにする。
4. **全 cue に `beat` / `emotion` / `speed` を置く。** 顔は `beat` から解決される
   （`face` は既定から外す所だけ明示）。
5. **聞き手の反応を置く。** `react.<id>.beat` で顔が決まる。記号は山場に絞る。
6. **`pause_before` を調整する。** 0.15〜2.2 秒。速度の切れ目に置く。
7. **`acting.py audit` を回す。** 警告のうち、作品の意図と合わないものは残してよい。
   ただし理由を `plan.md` に書く。
8. **`report` を残す。** 旧版と `compare` する。

## 例（2 行の掛け合い）

```yaml
- name: c009
  character: mirabo
  line: "99.8%です。"
  emotion: confidence
  beat: pride
  face: excited
  speed: fast
  pause_before: 0.35
  volume: normal
  react:
    mirai: {face: worried, mark: "？", beat: doubt}

- name: c010
  character: mirai
  line: "その数字は、何を測った。"
  emotion: neutral
  beat: doubt
  face: thinking
  speed: slow
  pause_before: 0.6
  volume: quiet
```

この 2 行で、機体は当てて浮かれ、人は疑い、記号がその疑いを一瞬だけ外へ出す。
`face` は人物票の `pride` / `doubt` から解決されたもの。

## よくある失敗

| 失敗 | 直し方 |
| --- | --- |
| 全部の cue に同じ `speed` | 山場と静かな所で分ける。最長連続 25% 未満 |
| 全部の cue に同じ `beat` | 人物票の感情を場面ごとに選び直す。顔も動きも単調になる |
| 記号を 20 か所以上 | 山場 8〜15 か所に絞る。続けて置かない |
| 反応の顔が話し手と同じ | その人物の人物票（`emotions`）から選ぶ |
| `pause_before` が 0.3 秒ばかり | 沈黙の所だけ 1.2〜2.0 秒へ |
| 感情を台詞で名指し | 動作・間・反応へ移す |
| 声の欄だけで感情を作る | 顔・身体・反応を先に決める |

## 検査の読み方

```
<venv> engine/acting.py audit --project projects/<作品>
```

```
beat       132/148  89%
face       140/148  95%（明示 140 / 95%）
聞き手の顔  94/148  64%
記号         11 か所
速度       5 語 / 最長連続 14（9%）
間         0.15〜2.0 秒（中央 0.4）
```

- `beat` と `face` が 90% 未満 → 抜けている cue を埋める。
- `聞き手の顔` が 60% 未満 → 反応の置き所を増やす。まず顔だけ。
- `速度` が 4 語未満 → `slow` / `fast` の外へ。
- `間` の幅が狭い → 章の転換と山場の前に長い沈黙を置く。
- `記号` が 8 未満 → 山場に足す。15 超 → 削る。
- 同じ人物に記号が続く → 間に別の人物の反応を挟む。
