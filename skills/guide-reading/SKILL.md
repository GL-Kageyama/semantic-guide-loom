---
name: guide-reading
description: 表示文とは別に、声に読ませるための読み（かな）を reading.yaml に用意する。engine/reading.py の draft で下書きし、数字・%・Latin・日付の罠を人が直し、audit と phonemize で誤読を確かめる。make.sh は読みがあるときだけ build/<作品>/ に舞台を作り、作品のファイルは書き換えない。
argument-hint: '作品の置き場。例: projects/<作品>'
---

# guide-reading — 読みを間違えない

字幕と、声に読ませる文は、別に持つ。**字幕は原表記のまま。読みだけ、かなにする。**
読みを台本の `line` に直接書くと、字幕までかなになる。だから `reading.yaml` を分ける。

```
script.yaml / video.yaml   表示（漢字・数字・Latin）
        ↓ 人が決める
reading.yaml               声に読ませる読み（かな）
        ↓ engine/reading.py stage
build/<作品>/script.yaml   line だけ読みに差し替え
build/<作品>/video.yaml    display に元の表記を補う
```

## 手順

1. **下書きを作る。**
   ```
   <venv> engine/reading.py draft --project projects/<作品>
   ```
   `reading.yaml` ができる。`needs_review` に、数字・`%`・Latin を残した cue が並ぶ。
   既にある読みを消さないよう、上書きは `--force` のときだけ。

2. **人が決める。** `needs_review` の cue を上から見る。数字・百分率・年号・固有名は、
   文脈で読みが変わる。**機械に決めさせない。**
   - `97%` → `きゅうじゅうななぱーせんと`
   - `2025年7月` → `にせんにじゅうごねんしちがつ`
   - `ChatGPT` → `ちゃっとじーぴーてぃー`
   - `AI` → `えーあい`（そのままでも読めるが、読みを固定した方が安定する）

3. **日付の罠を確かめる。** `draft` は `四月→しがつ / 七月→しちがつ / 九月→くがつ` と、
   `一日〜三十一日` の特殊読みを表で先に直す。それでも、`一日中`（いちにちじゅう）と
   `一日`（ついたち）のような文脈依存は残る。`references/reading-traps.md` を見る。

4. **監査する。**
   ```
   <venv> engine/reading.py audit --project projects/<作品> --strict
   <venv> engine/reading.py audit --project projects/<作品> --phonemize --cue c001
   ```
   `--strict` は警告があれば非 0。`--phonemize` は Tsukasa が実際に読む音素を出す。
   「世界の見方」が `せかいのみかた` になっているか、はここで見る。

5. **焼く。** `engine/make.sh` が `reading.yaml` を見つけると、自動で
   `engine/reading.py stage` を呼び、`build/<作品>/` に舞台を作る。
   声は `line`（＝読み）から作られ、字幕は `display`（＝元の表記）から出る。
   作品の `script.yaml` / `video.yaml` は**書き換えない**。

6. **声を作り直す。** 読みを変えたら、その cue の声だけ捨てる。
   ```
   <venv> engine/reading.py stage --project projects/<作品> --prune-voice
   ```
   `make.sh` は声を作る回だけ、これを自動で付ける。`SKIP_VOICE=1` の回は消さない
   （消すと声が無いまま混ざる）。全部作り直すなら `FORCE=1`。

## 決まりごと

- **読みは音のためだけ。** 字幕・章題・`timeline.json` の `text` には渡さない。
- **外来語はカタカナでよい。** ひらがなに開く必要はない。Tsukasa が読めればよい。
- **句読点は残す。** 間と息継ぎは句読点から作られる。
- **ルビ（`漢字《かな》`）と reading.yaml を混ぜない。** 読ませ方は reading.yaml に一本化する。
  ルビは reading.yaml が無い作品のための後方互換。
- **`display` を消さない。** 舞台は、読みに差し替えた cue の元表記を `display` に補う。

## 参照

- 日付・数・固有名の罠 → `references/reading-traps.md`
- 声の道具（正本） → `semantic-audio-loom` の `build_voice.py`
