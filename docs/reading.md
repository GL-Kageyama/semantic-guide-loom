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

`--prune-voice` は `assets/voice/<cue>.params.yaml` の `reading` か `dialogue` が
新しい読みと違う cue の WAV だけを消す。`make.sh` は声を作る回だけ付ける。

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
