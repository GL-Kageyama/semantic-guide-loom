# 継ぎ目 — `mix.yaml`・`timeline.json`・`faces.json`

5 つの段は **4 つのファイルで継がっている**。段をまたぐ受け渡しは、この 4 つにしかない。

```
script.yaml ──(build_voice)──> voice/*.wav ──(assemble)──> mix.yaml + renders/<name>.wav
     │                                                          │
     │                                                    (export_timeline)
     │                                                          ↓
     └───────────────────────────────────────────> timeline.json
                                                                 │
video.yaml ──(template / cast の名)───────────────────────────────┤
                                                                 ↓
                                          (render) ──> projects/<作品>/renders/<name>.mp4
```

この 4 つに**任意の 5 つ**が重なる。どれも無ければ、従来の 5 段のまま動く。

```
reading.yaml ──(reading.py stage)──> build/<作品>/script.yaml + video.yaml
                                          ↑ line を読みに、display に原表記
bgm.yaml ──(bgm.py generate / mix)──> assets/bgm/<name>.wav + mix.yaml の bed と duck
research/ ──(scriptcheck が fact の参照を見る)──> video.yaml の details
characters/<id>.character.yaml ──(人は check / brief。engine は beat→face の解決にも読む)──> 台本と演技
characters/<キャスト>.persona.yaml ──(関係。人が読む)──> 掛け合いの型
```

**向きが一方通行であることが、この機構の要**。絵は音の実尺を読む。音は絵を知らない。
ゆえに台本を書き換えても、絵の側の時刻を手で直す必要はない。

## `mix.yaml` — 組み立ての結果（派生。手で編集しない）

`assemble.py` が `script.yaml` と `voice/` の実尺から書く。
`timeline.json` の時刻は、**このファイルの voice stem の `start` と WAV の長さ**から取る。

`bgm.yaml` がある作品では、`bgm.py mix` が bed の `gain_db` と `duck` を
`bgm.yaml` の `mix` で上書きする。**それも含めて `mix.yaml` は派生**で、手で編集しない。

⚠️ **`pause_before` を足し直して時刻を作らない。** `assemble.py` は各キュー頭尾の
無音を切るので、足し直すと 1 コマずつずれる。

## `timeline.json` — 音と絵の唯一の継ぎ目（派生）

`export_timeline.py` が書き、`render.py` だけが読む。

```json
{
 "name": "...", "project": "/abs/path/projects/cyber-basics",
 "title": "...", "channel": "...",
 "template": "dialogue-bust", "cast": "mirai-mirabo",
 "fps": 30, "width": 1280, "height": 720, "duration": 287.27,
 "audio": "/abs/path/renders/cyber-basics.wav",
 "cues": [{"name": "c01", "character": "mirabo", "start": 2.0, "end": 3.1,
           "wav": "/abs/path/c01.wav", "text": "ミライさん！",
           "emotion": "excitement", "face": "excited", "beat": "pride",
           "react": {"mirai": {"face": "thinking", "beat": "doubt", "mark": "？"}},
           "chapter": 0}],
 "chapters": [{"cue": "c01", "index": 0, "label": "序章", "title": "...",
               "start": 0.4, "cue_start": 2.0, "...": "型が読む欄は素通し",
               "details": [{"cue": "c03", "head": "...", "lines": ["..."],
                            "fact": "...", "start": 9.74}]}]
}
```

**`details` の `start` は `mix.yaml` の voice stem の実尺**（`export_timeline.py` が
`cue` を解決して足す）。`timeline.json` は cue 名を引かずに自己完結する。
`details` を持たない章には、この欄を**足さない**（従来の形を変えない）。

`wav` は**キュー単体の WAV**。口の動きはこの 1 本の包絡から作る——
`duration` の WAV から切り出すのでなく、cue ごとのファイルを測る。

`face` / `react` は**解決済み**の値が入る（明示 `face` → `beat` → `emotion` の
対応表 → 既定）。`beat` もそのまま残るが、絵は読まない（監査と記録のため）。

`project` は作品の置き場。`render.py` が、書き出し先を決め損ねたときの既定
（`<project>/renders/<name>.mp4`）に使う。

## `faces.json` — 切り出した素材（派生）

`prepare_assets.py` が `build/<作品名>/assets/` に書く。`render.py` と `Cast` が読む。
シートから測った口の錨（`pt`）と、表情 → 画像ファイルの対応表が入る。
表情シートそのものは `references/sheets/`（入力。Git LFS）。

## 派生を置く場所

`mix.yaml`・`timeline.json`・`faces.json` はどれも焼き直せば戻る。
`build/` と一緒に `.gitignore` の側にあり、作品の `renders/`（成果物）とは別
（[placement.md](placement.md)）。
