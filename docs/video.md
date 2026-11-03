# `video.yaml` — 映像の台本（作品が持つ）

音には渡さない。`export_timeline.py` が読み、`timeline.json` に写す。

```yaml
title: 脆弱性とサイバー攻撃
subtitle: なぜ、同じ三つなのか
channel: MIRAI × MIRABO
template: dialogue-bust        # references/templates/<name>/ の名
cast: mirai-mirabo             # characters/<name>.cast.yaml の名。人物を置かない型は書かない
width: 1280                    # 省略時 1280
height: 720                    # 省略時 720
fps: 30                        # 省略時 30
chapters:                      # cue の名 → 章
  c07:
    label: 第1章
    title: 入力が、命令になる
    term: 入力
    key: "信じた文字列が、\n実行される。"
    details:                   # 任意。章の中で切り替わる詳細カード
      - cue: c09               # この章の cue。この頭で切り替わる
        head: 命令の形
        lines: ["一文に、一つの動作", "目的語を先に置く"]
        fact: input-command-form   # research/facts.yaml の id（任意）
display:                       # cue の名 → 字幕の文（原表記）
  c05: "20年も？"
```

- **`chapters` の中身は型が決める。** `export_timeline` は `details` の `cue` だけを
  時刻へ解決し、他は素通しする。`dialogue-bust` は `term` / `key` / `details` を読み、
  `narrate-slide` は `bullets`（配列）を読む。型の欄は [templates.md](templates.md)。
- **`details`** は `cue` / `head` / `lines`（1〜4 項目）が必須で、`fact` は任意。
  `cue` は**その章の範囲**（章の頭 cue 以上、次の章の頭 cue 未満）にあり、台本順に
  増えること。`head` と `lines` は改行せず、`lines` の各項目を 1 表示行に割っておく。
  **詳細の無い章・作品は、従来どおり `key` 1 枚**で焼ける（後方互換）。
- **検査の分担。** `scriptcheck.py` は形・所属・順序・容量・fact の参照を見る
  （古い `mix.yaml` でも走る）。実尺が要る検査——次のカードまでの可視時間
  **4.0 秒未満**、章の `start` より前、最初のカードが章の頭 cue と同じ——は
  `export_timeline.py` が**警告**として出す（TTS の実尺で変わるため止めない）。
- **`display` は「音の表記」と「字幕の表記」を割るための欄。** `line` はカタカナで
  読ませ、字幕は原表記で出す、という使い方をする。無い cue は `line` がそのまま出る。

## `chapters.yaml` — 章の頭（音が持つ）

```yaml
- c01
- c07
```

cue の名の配列。`assemble.py` がこの cue の手前にチャイムを置く。
**`video.yaml` の `chapters` とは別物**——あちらは絵の札、こちらは音の合図。
