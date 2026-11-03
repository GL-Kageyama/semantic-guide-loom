# `bgm.yaml` — 敷き音の意図（作品が持つ。任意）

話から決めた意図と、ミックスの値を持つ。**音そのものは `assets/bgm/<name>.wav`。**

```yaml
name: underlay
prompt: "A continuous soft ambient pad, warm evolving chords, ... no drums, no vocals"
mood: [calm, curious, unease]
duration: 90            # assemble が全体長へ継ぎ足すので 90 秒で足りる
segment_s: 30           # MusicGen の上限
seeds: auto             # prompt の SHA1 から決定的に。または整数の配列
crossfade_s: 2.5
level_gain_db: 8.0
level_limit: 0.95
provider_settings: {tokens: 1500, guidance_scale: 3.0}
mix:
  gain_db: -8.0
  duck: {threshold_db: -30, depth_db: 3.0, attack_s: 0.03, release_s: 0.45}
```

- `engine/bgm.py generate` は `assets/bgm/<name>.params.yaml` の `input_sha1` を見て、
  入力が変わったときだけ作り直す。`--force` / `BGM=force` は常に作り直す
- `engine/bgm.py mix` は `assemble.py` が書いた `mix.yaml` の bed `gain_db` と
  `duck` を `mix.gain_db` / `mix.duck` へ直し、SAL の `bin/mix.py` で混ぜる
- **`mix.yaml` を手で直さない。** 直しても次の `make.sh` で戻る。正本は `bgm.yaml`
- 形は `schemas/bgm.schema.json`

## 音量と ducking は `bgm.yaml` が持つ

声の下へ潜らせる量（`mix.duck`）も、敷き音そのものの大きさ（`mix.gain_db`）も、
`bgm.yaml` の `mix` が決める。`mix.yaml` はその結果を書かれるだけの派生である。

**声量とは別の層。** 声の大きさは台本の `volume` と semantic-audio-loom の
ピーク正規化が持ち、ここは BGM がどれだけ下がるかだけを持つ。

## 道具

```bash
engine/bgm.py suggest  --project projects/<作品>     # bgm.yaml の下書き
engine/bgm.py generate --project projects/<作品>     # assets/bgm/<name>.wav を作る
engine/bgm.py mix      --project projects/<作品> --stage <台本の場所>
```

`make.sh` は `BGM=auto`（既定）で、`bgm.yaml` があり、入力が変わったときだけ
`generate` を走らせる。`BGM=0` でこの段ごと飛ばす（[usage.md](usage.md)）。
