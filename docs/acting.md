# 演技 — 台詞より先に設計する

感情の弧（`review/acting/plan.md`）を置き、cue に `beat` / `speed` / `pause_before` /
`volume` / `react` を振る。**顔は `beat` から人物票を引いて決まる**（`face` は動かす
所だけ明示）。**まばたきはしない。**

演技は声と絵の両方へ渡る。声の側の意味は semantic-audio-loom が持ち、このリポジトリは
**同じ欄から顔と反応を解決する**。

## 台本の欄

```yaml
- name: c009
  character: mirabo
  line: "99.8パーセント。"
  emotion: confidence       # 声（SAL の 11 感情）
  beat: pride               # 演技の正本。人物票の感情キー
  face: smile               # 省略可（明示があれば beat より優先）
  speed: fast
  pause_before: 0.3
  volume: normal
  react:                    # 聞き手の反応（この cue の間）
    mirai: {beat: doubt, mark: "？"}
```

- **`beat` が演技の正本。** `face` は省略してよく、人物票の `emotions.<beat>.face`
  から解決される。明示 `face` があればそちらを優先し、どちらも無ければ
  `cast.yaml` の `by_emotion[emotion]` に落ちる。
- `react` の id は cast の id。`face` / `beat` は cue と同じ規則で解決され、
  `mark` は 3 文字まで。**顔だけ・記号だけでもよい**が、どちらも無い反応は無効。
- **解決するのは `export_timeline.py` の 1 か所だけ**（規則は
  `engine/characters.py`）。`timeline.json` には解決済みの `face` と
  `react.<id>.face` が入り、`beat` も記録として残る。絵を描く側は推測しない。

人物票の `emotions` の形は [characters.md](characters.md)。

## 検査と計測

```bash
engine/acting.py audit --project projects/<作品>        # 参照切れ・網羅・単調さ
engine/acting.py audit --project projects/<作品> --strict --json
engine/acting.py report --project projects/<作品> --out review/acting/v3.yaml --version v3
engine/acting.py compare --before review/acting/v2.yaml --after review/acting/v3.yaml
```

`audit` は演技の欄の参照切れを見て、感情の振れ幅（網羅と単調さ）を測る。
`make.sh` はキャストを名乗る作品だけ、焼く前にこれを走らせる。`STRICT=1` で警告も
失敗にする。

**計測は `review/acting/` に置く。** `review/reports/` に混ぜない
（[review.md](review.md)）。

## 描画 — 何を読むか

描画は `timeline.json` の**解決済み** `face` / `react` を読む。`beat` から顔は
推測しない（解決は `export_timeline.py` の役目）。

```yaml
# references/templates/<型>/template.yaml の acting 節
acting:
  reaction:
    lead: 0.20             # 相手の cue の頭より何秒早く反応を出すか
  mark:
    size: 42               # 720p 基準
    bold: true
    color: [255, 209, 102, 235]
    outline: [12, 20, 36, 230]
    outline_width: 3
    pop: 0.16              # 出るまで（拡大しながら alpha を上げる）
    hold: 0.85             # 保つ
    fade: 0.32             # 消える
    pop_amp: 0.55          # 出るときの最大拡大（1 + これ）
    rise: 10               # 浮き上がる画素
    anchor:                # slot の原点からの相対位置 [x, y]
      left: [360, 10]
      right: [160, 0]
```

**`acting` が無ければ、反応も記号も描かない**（古い作品は今までどおり）。

### 顔の切り替え

- 人物ごとに「表情が変わる時刻の列」を `build()` で 1 度だけ作り、各フレームは
  `bisect` で引く。**1 コマは状態を持たない。**
- 列に載るのは 2 種類。**自分の発話の頭**（cue の `face`）と、**他人の cue の
  `react[cid].face`**（時刻は `cue.start`。記号だけ `reaction.lead` だけ遅れる）。
- 同じ時刻なら**発話が勝つ**。それ以外は**遅い方**が勝ち、次にその人が顔を
  変えるまで保つ。
- `face` の無いコマは `cast.by_emotion[emotion]`、それも無ければ
  `default_expression` に戻る（古い作品のため。新しい作品は `beat` で決まる）。
- **まばたきはしない。** `blink` はデータとして残っているが、描画は読まない。

### 記号の時間

- `t0 = cue.start + reaction.lead`。`pop → hold → fade` の順に alpha と拡大を
  決め、`t0 + pop + hold + fade` か**その人が次に話す cue の頭**の早い方で終わる。
- 自分が話し始めたら記号は出さない（発話が優先）。
- 位置は slot の原点 + `anchor[slot]` + 身体の揺れ。`rise` は `hold` の間だけ
  上へ動く。**紙吹雪・乱数・時刻以外の状態は使わない。**

### 感情による身体

`cast.yaml` の `motion_gain`（表情 → 倍率）を、`motion` の揺れに掛ける。

```yaml
motion_gain:
  surprised: 1.3
  worried: 0.7
  sad: 0.4
```

**掛けるのは明示の `face` があるコマだけ。** `by_emotion` の既定で描く古い
作品の揺れを変えないため。未記載は 1.0。`0` 以下は無効。
