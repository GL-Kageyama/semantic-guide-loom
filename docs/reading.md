# `reading.yaml` — 読み（作品が持つ。任意）

声に読ませる文だけを持つ。**字幕・章題・`timeline.json` の `text` には渡さない。**

```yaml
name: black-swan-ai
readings:
  c001: "みらいさん。『ぶらっくすわん』って、くろいはくちょうのこと、ですよね？"
  c250: "にせんにじゅうにねんじゅういちがつみっか"
needs_review: [c007, c250]      # 数字・%・Latin を残した cue（人が決める）
```

- `readings` … cue の名 → 声に読ませる文（かな。外来語はカタカナ可）
- 句読点・`……`・`？`・`！` は残す（間と抑揚がそこから作られる）
- `engine/reading.py draft` が下書きし、`audit` が残存漢字・数字・`%`・Latin を見る
- 形は `schemas/reading.schema.json`

**読みは音のためだけ。** 字幕・章題には渡さない（字幕は `video.yaml` の `display`）。

## 読みの舞台 — `build/<作品>/`

`make.sh` は `reading.yaml` があるときだけ、2 の前に `reading.py stage` を呼ぶ。

```
projects/<作品>/script.yaml ─┐
projects/<作品>/video.yaml  ─┤ stage
projects/<作品>/reading.yaml ┘
        ↓
build/<作品>/script.yaml   line = readings[cue]
build/<作品>/video.yaml    display[cue] = 元の display か line（原表記）
build/<作品>/chapters.yaml / voice_fx.yaml / sfx.yaml / bed_mute.yaml
```

**作品のファイルは書き換えない。** 声は舞台の `line` から、字幕は舞台の `display` から
出る。`export_timeline.py` の `name` と `render.py` の資材の道が揃うよう、舞台は
`build/<作品名>/` に作る（`<作品名>` は作品ディレクトリの basename）。

`--prune-voice` は `assets/voice/<cue>.params.yaml` の `reading` / `dialogue` か
**`character`** が新しい台本と違う cue の WAV を消す。話者を `mirai` から
`narrator` へ移したときも、声を作り直す。`make.sh` は声を作る回だけ付ける。

## TTS の罠

Tsukasa は、かなに直したあとで前処理の置換をする
（`Utils/phonemize/cotlet_utils.py`）。正しいかなを書いても、次の語は崩れる。

- `すうは` → `かずは`。`そすうは` は `そかずは`、`ふたごそすうは` は
  `ふたごそかずは`、`こすうは` は `こかずは`。
  → `素数は`・`双子素数は`・`個数は` は**漢字で書く**。
- `はつか` → `わつか`、`ななまんはっせん` → `ななまんわせん`。
  → 数字は `ハツカ`、`ナナマンハッセン` のように**カタカナで固定する**。
- `ふかつせい` は促音が落ちる → `フカッセイ`。
- `保型形式`・`原始根` は漢字だと `ほがたけいしき`・`げんしね`。
  → `ほけいけいしき`・`げんしこん` の**かなのまま**。

`audit` は `すうは` と `ふかつせい` を警告する。`--phonemize` で音素を確かめる。

## 分数

- **`A/B` は「B分のA」。** `1/2` → `ニブンノイチ`。
- **`x/log x` は「ログエックス分のエックス」。** `エックス分のログエックス` は逆。
- `√x log x` は積。`ルートエックス ログエックス`。分数にしない。

## ルビとの関係

`reading.yaml` の無い作品は、`script.yaml` の `line` に工房の記法 `漢字《かな》` を
書いて読み違えを塞げる。**両方を同じ作品に混ぜない。** ルビは後方互換で、
読みを本気で直すなら `reading.yaml` を使う（[script.md](script.md)）。

## 道具

```bash
engine/reading.py draft --project projects/<作品>     # display から下書き
engine/reading.py audit --project projects/<作品>     # 欠落・残存・字幕の長さ
engine/reading.py stage --project projects/<作品> --stage build/<作品>
```
