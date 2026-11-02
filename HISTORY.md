# HISTORY

## 0.3.0 — 2026-11-03 台本づくりを、設計から焼くまでつないだ

black-swan-ai を作ったとき、台本の設計・生成と評価の往復・キャラの一貫性・読みの補正・
BGM の生成は、すべて会話の中の手作業だった。同じやり方を次の作品でも再現できるよう、
**判断を伴う工程を 5 つのスキル**に、**決定的にできる工程を `engine/` の道具**に分けた。

**engine は LLM を呼ばない。** 同じ入力から同じ結果が出る。

### 足したスキル

| スキル | 何をするか | 作るもの |
| --- | --- | --- |
| `guide-design` | 本文より先に設計。評議会の plot モードで 60 超 | `design.md` |
| `guide-cast` | 採用台本から言葉の設定を起こす | `characters/<キャスト>.persona.yaml` |
| `guide-script` | 生成 → 8 次元評価 → 改稿の往復。60 超の最高版を採用 | `台本.md` → `script.yaml` ほか |
| `guide-reading` | 声に読ませる読みを、表示文と分けて持つ | `reading.yaml` |
| `guide-bgm` | 話に合わせて敷き音を毎回作る | `bgm.yaml` → `assets/bgm/underlay.wav` |

入口（`semantic-guide-loom`）に全体の流れと各スキルへの導線を足した。
`install.sh` の `SKILLS` と `.claude/skills/` の symlink も 6 本になった。

### 足した道具

| 道具 | 何をするか |
| --- | --- |
| `engine/persona.py` | `check`（cast との id・必須欄）・`brief`（人物票）・`analyze`（既存台本の話し方の実測） |
| `engine/review.py` | `table`（版ごとの平均の推移）・`record`（`review/scores.yaml`）・`validate`（評価 JSON） |
| `engine/reading.py` | `draft`（fugashi でかなに開く）・`audit`（残存漢字・数字・phonemize）・`stage`（ビルド用の舞台） |
| `engine/scriptcheck.py` | cue・章・display・読みの参照切れ、27 字超の字幕、声を持たない行、チャイムの欠け |
| `engine/bgm.py` | `suggest`（意図の下書き）・`generate`（MusicGen 30 秒 × 3 + クロスフェード）・`mix`（bed と duck の上書き） |

`schemas/` に `persona` / `reading` / `bgm` を足し、`tools/check_layout.py` の検査対象に
入れた。`characters/mirai-mirabo.persona.yaml` と `projects/black-swan-ai/bgm.yaml` を
加えた（前者は採用版 v7 から、後者は既存の underlay と同じ意図）。

### 決めたこと

- **ペルソナとキャストを分ける。** `cast.yaml` は画面の誰か、`persona.yaml` は言葉の誰か。
  cast の役目は増やさない。
- **読みは `build/<作品>/` の舞台で差し替える。** 作品の `script.yaml` / `video.yaml` は
  書き換えない。`line` に読み、`display` に原表記を残す。
- **BGM の正本は `bgm.yaml`。** `assemble.py` の bed −30 dB / duck 14 dB を
  `bgm.py mix` が上書きする。`mix.yaml` を手で直しても次の `make.sh` で戻る。
- **`reading.yaml` は既存作品にまだ足さない。** 足すと全 cue の声を焼き直すことになる。
  仕組みの検証は黒鳥のコピーに対する `draft` / `stage` で行った。
- **`semantic-audio-loom` の中身は書き換えない。** BGM は `AudioAssetEngine` と
  `bin/mix.py` をパスのまま呼ぶ。

### 検算

| 確かめたこと | 結果 |
| --- | --- |
| `engine/review.py table --project projects/black-swan-ai` | v4 57.13 / v6 64.50 / v6-single-model 62.38 / v7 67.25 採用 / v9 60.63 |
| `engine/persona.py analyze` | mirai 206 cue・平均 14.2 字、mirabo 122 cue・平均 13.4 字 |
| `engine/reading.py draft`（黒鳥のコピー） | 328 cue、`needs_review` 63（Latin の AI を含むため） |
| `engine/reading.py audit --phonemize --cue c027` | 「世界の見方」→ `せかいのみかた`（`sekai no mikata`） |
| `engine/reading.py stage` | 297 行を読みに差し替え、`display` 328 件を補完。作品ファイルは不変 |
| `engine/bgm.py generate --dry-run` | seeds `[21, 22, 23]`、30 秒 × 3 |
| `SKIP_VOICE=1 SKIP_ASSETS=1 ./engine/make.sh projects/black-swan-ai --still 40` | 336 stems / 904.0 秒、`renders/black-swan-ai.wav` 903.989 秒、bed −8 dB / duck 3 dB |
| `engine/scriptcheck.py --project projects/black-swan-ai` | 328 cue / 7 章、エラーなし（27 字超の字幕 14 件は警告） |

⚠️ **`review/README.md` の v4 を 57.12 → 57.13 に直した。** 8 次元の和 457 を 8 で
割ると 57.125。`engine/review.py` は `Decimal` の四捨五入で 57.13 を出す。
v7 67.25 と v9 60.63 は元の表と一致した。

### 通しのサンプル（`projects/hubble-mirror/`）で塞いだ穴

設計 → 人物 → 台本 → 読み → BGM → `make.sh` を 1 本通し、機構の穴を 4 つ直した。
サンプルは『ハッブルの鏡』（148 cue / 5 章 / 398.07 秒）。台本は評議会 8 次元の
平均 76.75 で v1 を採用（`review/README.md`）。

| 見つけたこと | 原因 | 直した所 |
| --- | --- | --- |
| 声の生成が `IndexError` で止まる | `……` だけの cue は声を持たず、Tsukasa の推論で長さ 0 になる | 沈黙は次の cue の `pause_before` に畳む。`scriptcheck.py` が声を持たない行をエラーにする。`guide-script` の「YAML へ起こす」にも規則を足した |
| 組み立てが `wave.Error: unknown format: 3` で止まる | `engine/bgm.py` が float32 で書き、`assemble.py` の `wave` が読めない | 書き出しを PCM 16 bit に固定し、形式を `input_sha1` に含めた（古い WAV は作り直される） |
| 章の頭が無音 | `chapters.yaml` があるのに `assets/sfx/chime.wav` が無く、`assemble.py` が黙って飛ばす | サンプルにチャイムを置き、`scriptcheck.py` が無いとき警告するようにした |
| チャイムを置いても聞こえない | 生成音の打音が 1.55 秒にあり、`assemble.py` の `shorten`（1.4 秒）で切れて打音が消える | 打音を先頭へ切り出した `chime.wav` にした（`chime.params.yaml` に記録）。`semantic-guide-loom` の嵌まりどころにも書いた |

実測: 敷き音は会話より 13.3 dB 下（ギャップ中央値 −32.3 dB 対 声 −19.0 dB、
`gain_db: -8` / duck 3 dB）、ピーク −0.4 dBFS。章の印は 5 か所とも −10 dB 前後まで
上がる（敷き音 −20 dB の上へ約 10 dB）。映像は 1280×720 / 30 fps、字幕は最長 24 字。

## 0.2.0 — 2026-11-01 置き場を姉妹リポジトリに揃えた

`semantic-audio-loom` / `semantic-visual-loom` と同じ名のものが同じ場所に在る形へ寄せた。
**道具も台本も 1 行も変えていない。** 焼き上がりは移す前とバイト一致。

### 移したもの

| 前 | 後 | 理由 |
| --- | --- | --- |
| `works/<作品>/` | `projects/<作品>/` | 姉妹が `projects/`（audio の生成物・visual の作品も同じ） |
| `assets/<作品>/`（トップ） | `projects/<作品>/assets/` | 作品は 1 か所に閉じる（audio も `projects/<p>/assets/`） |
| `out/<作品>.mp4` | `projects/<作品>/renders/<作品>.mp4` | 成果物も作品の隣（visual の `renders/` に倣う） |
| `templates/<型>/` | `references/templates/<型>/` | 姉妹の `references/` は「再利用する元」 |
| `sheets/` | `references/sheets/` | 同上 |
| `casts/<名前>.cast.yaml` | `characters/<名前>.cast.yaml` | 姉妹は `characters/`（audio の声の人物） |

⚠️ **`assets/renders/`（assemble.py が書く中間の WAV）と、作品の `renders/`
（焼いた MP4）は別物。** 前者は `.gitignore`、後者は成果物で LFS。

### 足したもの

| ファイル | 何 |
| --- | --- |
| `install.sh` | 姉妹と同じ `--local` / `--global` / `--uninstall`。`.claude/skills/` へ相対で張る |
| `.claude/skills/semantic-guide-loom` | `--local` が張るのと同じ symlink（clone した時点で効く） |
| `references/README.md` | `references/` が何を持つか（型・表情シート） |
| `schemas/video.schema.json` ほか 2 本 | `video.yaml` / `template.yaml` / `cast.yaml` の形 |
| `schemas/README.md` | `script.yaml` の形の正本は audio の `schemas/scene.schema.json`。**ここへ写さない** |
| `tools/check_layout.py` | 古い綴りが残っていないか・`schemas/` が実物に通るか |
| `assets/repo-hero.png` + `assets/README.md` | README の頭の絵。**外で描いていない**——`cyber-basics` の 29.0 秒のコマ |

`timeline.json` に `project` を足した（`render.py` が書き出し先の既定を決めるのに使う）。

### 多言語化はしないと決めた

姉妹は `README-ja.md` / `README-zh.md`・`docs/*-ja.md`・`locales/` を持つが、この
リポジトリには置かない。成果物が日本語の音声と字幕であること、台本を他言語で書けば
同じ手順で焼けること——が理由。**仕組みとしての翻訳・言語切替は作らない。**
README「言語」と `CLAUDE.md` に明記した。取り込むのは別の段。

### 検算

移した後に 2 本とも焼き直し、**バイト一致**を確かめた。

| 作品 | 焼き直し | 移す前の記録 | 一致 |
| --- | --- | --- | --- |
| `cyber-basics` | md5 `c1de4b4ae16b0e6d087f78ea4a812301` / sha256 `dc0d3b90…` | sha256 `dc0d3b904778131585ba375bd81e6493064539ccd0faf326cfdee5affdbcf222` | ✅ |
| `making-a-guide` | sha256 `c4a3ebad59b4c0accbf59a8ce1b859c8f35794abd8c363077450a59a4e715779` | 同（LFS の oid） | ✅ |

`SKIP_VOICE=1`（声を作り直さず、clone しただけの状態）で回した。97 cues / 5 chapters /
287.3 秒は 0.1.3 と同じ。

## 0.1.3 — 2026-11-01 資材を洗い出し、声まで入れた

台本を `works/cyber-basics/` へ、音の資材を `assets/cyber-basics/` へ入れた。
**これで clone しただけでも、声を作らずに同じ mp4 が出る。**

### 洗い出し — この動画を作るのに何が要るか

| 段 | 要るもの | いまどこに在るか | 入れたか |
| --- | --- | --- | --- |
| 1 素材 | 表情シート 2 枚 | `資料/…/キャラ/` の原本 | ✅ `sheets/`（0.1.1） |
| 2 声 | 声 104 本 + `.params.yaml` 104 | audio の `assets/cyber-basics/voice/` | ✅ `assets/cyber-basics/voice/`（15 MB） |
| 2 声 | 声のプロファイル・参照音声 | `semantic-audio-loom/characters/` | — 声を作り直すときだけ要る |
| 3 組み立て | 台本 4 本（script / video / chapters / voice_fx） | audio の `projects/longform/cyber-basics/` | ✅ `works/cyber-basics/` |
| 3 組み立て | 鐘 `chime.wav` | audio の `assets/cyber-basics/sfx/` | ✅ `assets/cyber-basics/sfx/`（517 KB） |
| 3 組み立て | 敷き音 `underlay.wav` | audio の `assets/cyber-basics/bgm/` | ✅ `assets/cyber-basics/bgm/`（2.6 MB） |
| 4 時刻 | `mix.yaml` の実尺 | `assemble.py` が書く | 派生 |
| 5 描画 | 型・キャスト | このリポジトリ（0.1.0 から） | ✅ |
| 5 描画 | 書体 BIZ UD ゴシック | macOS のシステム | — 環境（`template.yaml` が名前で指す） |

**入れないもの（すべて焼き直せば戻る）**: `voice_trim/`（無音の切り詰め）・`voice_fx/`
（効果を掛けた声）・`chime_short.wav`（1.4 秒に切った鐘）・`underlay_tiled.wav`
（287 秒に延ばした敷き音）・`renders/cyber-basics.wav`（50 MB のミックス）・`build/`・
`mix.yaml`。

### 検算 — 声を消した状態で、同じ mp4 が出るか

`assets/` に `voice/` `sfx/chime.wav` `bgm/underlay.wav` だけを置き、
`voice_trim/` `voice_fx/` `*_tiled.wav` `*_short.wav` `renders/` を持たない状態で回した。

```
SKIP_VOICE=1 ./engine/make.sh works/cyber-basics
```

- `mix.yaml` … **103 stems / 287.3 秒**（元と同じ）
- `timeline.json` … **97 cues / 5 chapters / 287.3 秒**
- `out/cyber-basics.mp4` … **md5 `c1de4b4a…`（元と一致）**、42 秒

ゆえに `voice_trim/` 以下の 5 種は本当に派生で、持たなくてよい。ミックスの利得と頭出し
まで一致したので、声さえ在れば音の組み立ても再現できる。

### 決めたこと

- **`make.sh` は `assets/<作品>` があればそこを資材の根にする**（無ければ従来どおり
  `build/<作品>/audio`）。派生は `assets/` の中にも書かれるが `.gitignore`。
- **`FORCE=1` を付けると、入っている声を作り直す。** 生成先は `assets/<作品>/voice/`
  なので、**記録として入れた声が上書きされる**。台本を変えたときだけ使う。
- 事実の出どころ（`資料/…/資料_脆弱性とサイバー攻撃_2026.md`）は**入れていない**。
  私的なノートなので、入れるかは裁定が要る。

## 0.1.2 — 2026-11-01 本編『サイバー基礎』を guide-loom から焼き直した（バイト一致）

`out/cyber-basics.mp4`（4 分 47 秒・8,618 コマ・13,659,717 B・h264 + aac）を加えた。

**これは `資料/…/解説動画の作成_構想/試作/out/cyber-basics.mp4` の写しではない。**
guide-loom の `render.py` で焼き直したもので、**md5 が元と一致した**（`c1de4b4a…`）。
`--still` 3 枚の一致より強い検算——8,618 コマすべて同じ絵が出たことになる。

素材の側の居場所:

| 素材 | どこへ |
| --- | --- |
| 表情シート 2 枚 | `sheets/`（0.1.1 で移した。md5 一致） |
| 切り抜き 33 ファイル | **移さない**（`build/` に同じものが出る）。PNG 32 枚は md5 一致、`faces.json` は中身同一でキーの並びだけ違う |
| 声とミックス | `semantic-audio-loom/projects/longform/` のまま（そこが正本） |

焼き直しは `render.py` の 1 段だけ。時刻は既に在る `build/cyber-basics/timeline.json`
（`audio` が指すミックスは audio 側の `renders/cyber-basics.wav`）から取った。38.6 秒。

## 0.1.1 — 2026-11-01 大きなものは Git LFS に入れる

**入れるのは「入力」と「成果物」、入れないのは「中間物」。**

| 置き場 | 前 | 後 |
| --- | --- | --- |
| `sheets/*.png`（表情シート） | `.gitignore`（配布しない） | Git LFS で入れる |
| `out/*.mp4`（焼いた動画） | `.gitignore` | Git LFS で入れる |
| `build/<作品>/`（中間物） | `.gitignore` | `.gitignore`（変えず） |

`build/` は焼き直せば戻る。`out/` は焼き直さないと戻らない。シートに至っては
**切り抜きからは戻せない**——落とすと `dialogue-bust` が焼けなくなる。これが線の引き方。

`.gitattributes` は 0.1.0 の時点で `*.png` `*.mp4` を LFS にしていたので、変えたのは
`.gitignore` と説明の側だけ。実測は下の「入れたもの」。

実測:

- `sheets/ミライ_表情差分シート.png` … 2,068,863 B
- `sheets/ミラボ_表情シート.png` … 1,417,002 B
- `out/making-a-guide.mp4` … 1,724,933 B
- 3 つで約 5.0 MB。**すべて LFS のポインタで履歴に入る**（`git lfs ls-files` で確認）
- `build/` は 16 MB のまま `.gitignore`（入れない）

`works/*/mix.yaml` も `.gitignore` のまま。`assemble.py` が毎回書き直す派生だから。

## 0.1.0 — 2026-11-01 新設。解説動画の作り方を、型とキャストに割った

解説動画の試作（`資料/…/解説動画の作成_構想/試作/`、私的ノート）は 5 本のスクリプトで
1 本の動画を焼いていた。名前に `mirai` / `mirabo` が直書きされ、色と座標が定数で、
別の題材を焼くには写して書き換えるしかなかった。

**これは「置き場所が悪い」ではなく「どのリポジトリにも無い」問題だった。** 5 段のうち
2 段（声・組み立て）は `semantic-audio-loom` が正本だが、残る 3 段と `make.sh` は
私的ノートにしか存在しなかった。ゆえに新しいリポジトリを作り、3 段を持たせた。

### 分けたもの

| 分けた軸 | 前 | 後 |
| --- | --- | --- |
| 誰が画面に居るか | コードに直書き（`render.py` 8 箇所・`prepare_assets.py` 18 箇所） | `casts/<名前>.cast.yaml` |
| どう見えるか | コードに定数 | `templates/<型>/template.yaml` |
| どう並べるか | コードに 1 通り | `engine/layouts/<型>.py` |
| 何を話すか | 作品 | 作品（変わらず） |

型は**数**（YAML）と**並べ方**（Python）に割った。色違い・位置違いは YAML 1 枚で足り、
並べ方が違う型だけモジュールを 1 本足す。

### 忠実性の実測

作り直した `prepare_assets.py` と `render.py` が、元の試作と**同じ絵を出すこと**を
確かめてから先へ進めた。

- `faces.json` … 8 表情ぶんの `pt` / `line_span` / `line_y` がすべて一致。`by_emotion`・
  `lip` も一致
- 切り抜き 32 枚の PNG … **md5 がすべて一致**
- `--still` 3 時点（40 / 120 / 200 秒）… **バイト一致**（394,354 / 395,830 / 400,459 B）

レイアウトを `engine/layouts/` に割った後も、同じ 3 時点で**バイト一致**を再確認した。

### 受入試験 — 2 つ目の型で 1 本焼いた

`works/making-a-guide/`（『説明動画の作り方』）。型は `narrate-slide`、人物なし、
1920×1080 / 30fps、12 キュー・4 章・**51.0 秒**、1,605 コマ。声は
`semantic-audio-loom` の既製の `narrator`（`female_mature_p294`）。

題材をこの工房自身の手順にしたので、**社外の事実を一切名乗らない**見本になっている
（数を書けば実測として読まれるため）。

実測: 声 12 本 / 組み立て `mix.yaml` 12 stems / 声量の幅 **narrator 2.6 dB** →
中央値へ補正 / 描画 1,605 コマ / `out/making-a-guide.mp4` 1.7 MB（h264 + aac）。

### 音の道具に足した受け口（後方互換）

作品がこのリポジトリに在っても、声と WAV は `semantic-audio-loom/projects/longform/assets/<作品名>`
へ出ていた。作品を他所に置けるようにするため、2 本に `--assets` を足した。

- `projects/longform/explainer/build_voice.py` … `--assets <資材の根>`
- `projects/longform/assemble.py` … `--assets <資材の根>`

**既定は変えていない**（`--assets` を渡さなければ今までどおり）。`make.sh` は
`build/<作品名>/audio` を渡す。

### 決めたこと

- **時刻は mix.yaml の voice stem から取る。** 台本の `pause_before` を足し直さない。
- **字幕は `video.yaml` の `display`。** `line` は読みのためにカタカナで書く。
- **章の中身は型が決める。** `export_timeline.py` は `chapters` を素通しする
  （`dialogue-bust` は `term`/`key`、`narrate-slide` は `bullets`）。
- **表情シートは配布しない**（`sheets/*.png` を `.gitignore`）。機構でなく作品の絵であり、
  入れるかは作者の裁定だから。入れる場合は `.gitattributes` が `*.png` を LFS にしている。
