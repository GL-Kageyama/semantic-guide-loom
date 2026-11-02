# bgm.yaml の意図と、ミックスの実測

## 型

```yaml
name: underlay
prompt: A continuous soft ambient pad, warm evolving chords, very subtle felt piano
  notes, calm and curious, slight unease, steady background texture, no drums,
  no vocals, low dynamic
mood: [calm, curious, unease]
situation: A quiet explainer about black swans, prediction, and AI.
duration: 90
segment_s: 30
seeds: auto
crossfade_s: 2.5
level_gain_db: 8.0
level_limit: 0.95
provider_settings: {tokens: 1500, guidance_scale: 3.0}
mix:
  gain_db: -8.0
  duck: {threshold_db: -30, depth_db: 3.0, attack_s: 0.03, release_s: 0.45}
```

## prompt の書き方

MusicGen は「どんな音が鳴るか」の英文で学習している。属性の羅列より、**音の情景**を書く。

- 良い: `A continuous soft ambient pad, warm evolving chords, very subtle felt piano
  notes, calm and curious, slight unease, steady background texture, no drums, no vocals`
- 弱い: `calm, bgm, 60 bpm, C major`（音の説明になっていない）

**必ず入れる否定**: `no drums, no vocals`。解説の下では、リズムと声が会話を食う。
**展開を入れない**: `no build, no drops, no melody hooks`。1 本を全体に敷くため。

## 尺と分割

- `segment_s` は 30（MusicGen の上限）。`duration: 90` なら 3 本。
- 3 本を `crossfade_s`（2.5 秒）で継ぐと、約 85 秒。`assemble.py` が全体長へ
  継ぎ足す（`underlay_tiled.wav`）ので、90 秒で足りる。
- 作品が 90 秒未満のときだけ `duration: auto`。`mix.yaml` の実尺を読む。

## シード

- `seeds: auto` … prompt の SHA1 から、本数ぶん決定的に作る。同じ prompt なら同じシード。
- 手で振るなら 3 本。`[21, 22, 23]` のように並べる。
- シードを変えると音は変わるが、**prompt が同じなら雰囲気は近い**。採用したら
  `bgm.yaml` に残す（次に作り直したとき、同じ音に戻せる）。

## レベルの実測（black-swan-ai）

| 項目 | 値 |
| --- | --- |
| 会話の RMS | 約 −27 dBFS |
| BGM の RMS（bed −8 dB・+8 dB 後） | 約 −40 dBFS |
| 差 | 約 13 dB |
| ducking | 3 dB（閾値 −30 dBFS、attack 0.03、release 0.45） |

- `assemble.py` の既定は bed −30 dB / duck 14 dB。**そのままだと「ほとんど聞こえない」。**
- `gain_db` を上げすぎると、会話の子音が埋まる。13〜15 dB 下を目安に、耳で詰める。
- `level_gain_db` は生成音そのものの底上げ。`level_limit` でピークを切る（0.95）。

## 章ごとに変えない

1 本を全体に敷く。章の変化は、声・間・チャイム・絵で作る。曲を切り替えると、
継ぎ目で必ず「消えた／始まった」が聞こえる。どうしても変えるなら、章の頭ではなく
cue の間（`bed_mute.yaml` の穴）で切り替える。

## 作り直しの判定

`engine/bgm.py generate` は、`assets/bgm/<name>.params.yaml` の `input_sha1` を見る。
prompt・シード・分割・クロスフェード・利得・尺のどれかが変われば作り直す。
`--force` / `BGM=force` は常に作り直す。**採用した音は、意図ごと `bgm.yaml` に残す。**
