# `script.yaml` — 音の台本（作品が持つ）

semantic-audio-loom の scene 形式。`semantic-audio-loom/projects/longform/` の作品と
**同じもの**。1 cue = 1 行 = 1 つの声のファイル。**形の正本は
`semantic-audio-loom/schemas/scene.schema.json`**（このリポジトリに写しを置かない）。

```yaml
name: cyber-basics
default_pause: 0.25           # cue と cue のあいだの既定の間（秒）
cues:
  - {character: mirai, line: "入力、メモリ、依存。", speed: fast,
     pause_before: 0.35, name: c04}
```

- `character` … semantic-audio-loom の `characters/<id>.voice.yaml` の id
- `line` … **Tsukasa が読む形**。字幕とは別（[video.md](video.md) の `display`）
- `name` … cue の id。`mix.yaml` と `timeline.json` はこの名で継ぐ
- 演技の欄（`emotion` / `speed` / `pause_before` / `volume` / `pitch` …）は
  semantic-audio-loom の仕様。**効く欄は限られる**（semantic-audio-loom の
  `semantic-audio-loom/docs/resolve.md`「どの欄が、声を動かすか」を見る）

## 演技の欄 — 声と絵の両方へ渡る

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

演技の設計そのものは [acting.md](acting.md)、人物票は [characters.md](characters.md)。

⚠️ **読み違えは `line` のルビで塞ぐ。** 工房の記法 `漢字《かな》`。読みだけ仮名になり、
台詞と字幕は原表記のまま残る。ただし**読みを本気で直すなら `reading.yaml`**（下記）。
両方を同じ作品に混ぜない。ルビは `reading.yaml` の無い作品のための後方互換。

## `voice_fx.yaml` — 声の配色（任意）

声そのものではなく、帯域の処理を持つ。`assemble.py` が読む。**書いた人物だけ通す。**

```yaml
mirabo:
  highpass_hz: 220
  lowpass_hz: 6500
  gain_db: 1.5
  pitch_semitones: 3      # 半音。声帯だけでなくフォルマントも上がる
```

これは演技ではなく**配色の層**。小さな機体のスピーカーから出る声を、生の声と
ぶつからないようにする。変えたら `FORCE=1` で声を作り直す（既存の WAV は飛ばされる）。
