# HISTORY

## 0.5.2 — 2026-11-03 README の頭の絵を、リポジトリの顔として描き直した

`assets/repo-hero.png` は `projects/cyber-basics` の 29.0 秒のコマだった。リポジトリの
本質を 1 枚に畳んだ hero に差し替えた。絵は
`distill-essence-engine/examples/semantic-guide-loom/semantic-guide-loom-hero/` の
`input.md` / `prompt.md` から外で描いた。

- 中央のシンボルは**目盛りと型抜き**。声の波形が目盛りを刻み（時刻は音の実尺から）、
  穴の形が違う 2 枚の型抜きが同じ台本から別の絵を出し、抜けた光が切り離された
  1 コマを結ぶ（1 コマは状態を持たない）。白熱は枠の中の一点だけ。
- 姉妹 hero と同じ 4 色（紺・金橙・白熱・薄灰）。織機（`semantic-audio-loom`）と
  制作台帳（`semantic-visual-loom`）は既に使われているので、名前の比喩でなく機構から起こした。
- `assets/README.md` の由来を「外で描いた hero」に書き換えた。
- 実測（2026-11-03）: 1672×941。`git check-attr` で `filter: lfs`。

## 0.5.1 — 2026-11-03 文書を 13 本に分け、テストを足した

`docs/contract.md` と `docs/template-contract.md` の 2 本を、1 トピック 1 ファイルの
13 本へ分けた（usage / placement / design / research / script / video / reading /
bgm / characters / acting / templates / timeline / review）。索引は README の
「ドキュメント」表。README は現在の情報だけにし、細部は docs へ移した。冒頭は
「テーマが、台本になり、映像になる。」の 3 行。

- `requirements.txt` を足した（Pillow / numpy / scipy / PyYAML / jsonschema / pytest）。
- `tests/` を足した。`conftest.py` とテスト 8 本・33 件。`export_timeline` の実尺、`reading.py stage` が
  作品を書き換えないこと、`scriptcheck` の参照切れ、`bgm` の決定性、
  `render.py --still` の同一性、文書の相対リンクと索引を見る。
- 実測（2026-11-03）: `pytest -q` 33 passed（2.93 秒）、`tools/check_layout.py` rc 0。

## 0.5.0 — 2026-11-03 中央パネルの詳細カードと、調査から作る仕組み

`dialogue-bust` の中央パネルは、章の名・語（`term`）・章題・小さな言葉（`key`）を
1 枚に焼き、章の間ずっと同じ絵を貼っていた。`key` は章の問いを 2 行で置くだけで、
話が進んでも変わらない。ここを、**章のヘッダは残したまま、その下の本文だけが
章の中で切り替わる**形にした。掛け合いを楽しむ人にも、詳細を掴みたい人にも届く。
あわせて、解説動画の初手として**検索で情報を集め、台帳に格納し、動画作りに活かす**
仕組み（0 段・調査）を足した。**台本と声は v12 のまま**（`script.yaml` / `台本.md` /
`reading.yaml` / `bgm.yaml` を変えていない。309 cue / 5 章 / 1033.8 秒）。

### 調査を 0 段にした — `research/`

設計より先に、検索・取得・検証を行い、作品の隣に台帳を残す。**焼く時にネットを見ない**
（`make.sh` は検索も取得もしない）。

```
projects/<作品>/research/
  README.md  queries.md  sources.yaml  notes/<id>.md  facts.yaml
```

- `sources.yaml` は `id` / `title` / `kind`（official / paper / reference / news /
  in-work）/ `url` or `path` / `accessed` / `confidence`。`accessed` は
  **引用符で囲む**（PyYAML が日付オブジェクトに変えるため。`scriptcheck.py` が拾う）。
- `facts.yaml` は 1 fact = 1 主張。`sources` は 1 つ以上で `sources.yaml` を指す。
  作品内の予測・演出は `kind: in-work` として事実と分ける。
- `video.yaml` の `details[].fact` が fact の id を指す。カードの文は fact の範囲を出ない。
- 新スキル `skills/guide-research/`。検索語・当たった資料・**古い値の訂正**を
  `queries.md` に残す。`schemas/research.schema.json` と `scriptcheck.py` の参照検査
  （未知の fact・解決しない source・`confidence: low` の使用）を足した。
- 台帳は入力（テキスト）なので Git に入れる。`build/` へ移さない。

### 中央パネルを広げ、人物を左右へどけた

| 項目（720p） | 0.4.0 | 0.5.0 |
|---|---:|---:|
| 左の origin | `[14, 184]` | `[0, 184]` |
| 右の origin | `[918, 280]` | `[1020, 280]` |
| パネル box | `[510, 78, 906, 556]` | `[492, 78, 1006, 556]` |
| 幅 / 内側 | 396 / 328 | **514 / 446** |
| 左右の隙間 | 20 / 14 | **16 / 16** |
| 右の余白 | 136 | 34 |
| パネル中心 | 708 | 749 |

左はもともと余白が少ないので −14px、右は +102px。パネルは 2 人の間の中央
（`(476+1022)/2 = 749`）に置いた。右のリアクション記号の anchor は
`[200, 0]` → `[160, 0]`（新しい右 origin で 3 字が画布の右端を越えない位置）。

ヘッダ（label・tag・rule・term・title・short rule）を描く helper にまとめ、
**helper が本文の開始 y を返す**ようにした。`detail_geometry(ch)` は同じ helper を
測るだけ（`im=None`）で通すので、描画と容量の計算がずれない。実測（章題 1 行）:
本文開始 **375**、下端 **522**、容量 **4 行**、4 行で下端 **508**。章題 2 行なら
本文開始 415・容量 3 行。`head` 22px 太字（asc+desc=23）、`line` 22px / step 27。
23 枚 92 行の実測で、最長の head は **198px**、最長の行は **330px**（内側 446px）。

### 詳細カード

```yaml
details:
  - {cue: c045, head: ファーストライト, lines: [1990年5月20日, ...], fact: first-light}
```

- `cue` / `head` / `lines`（1〜4）が必須。`fact` は任意。**章に 2〜7 枚**、23 枚を 5 章へ。
- `cue` は**その章の範囲**、台本順に strict に増える。最初のカードは章の頭 cue より
  後ろ（`key` を読む時間）。可視時間の実測で最短は **5.21 秒**（c240→c241）。
- `export_timeline.py` が `cue` を `mix.yaml` の voice stem の `start` に解決し、
  `{**detail, "start": ...}` に差し替える。**timeline は cue 名を引かずに自己完結**する。
- `scriptcheck.py` が形・所属・順序・容量・事実の参照を見る。実尺が要る検査
  （可視 4.0 秒未満・章の外・最初が章の頭 cue と同じ）は `export_timeline.py` が
  **警告**にする（TTS の実尺で変わるため止めない）。
- 選択は `bisect_right(starts, t) - 1`（0 に clamp）。切替の `timing.detail_fade`
  （0.30 秒）だけ `Image.blend(prev, cur, smooth(age / fade))`。**章の切替では
  blend しない**（従来の slide だけ）。age=0 は前のカードが 100%。
- 詳細を持つ作品だけ、パネルを**箱 + 輪郭の数 px**（`outline_width + 2` = 4px）に
  切り詰めて持つ。切り詰め後 522×486×4B ≈ 0.97 MiB、28 枚で ≈ 27 MiB
  （フルキャンバスなら ≈ 99 MiB）。箱の外は完全透明で、slide 0 と 10 の貼り付けが
  フルキャンバスと**ピクセル一致**することを確かめた。フルキャンバスには戻さない。

### 後方互換と、意図した絵の変更

- **詳細機構を入れ、型を広げる前**に、v12 timeline の 40 / 200 / 400 / 700 / 900 秒の
  `--still` を描き、変更前の SHA-256 と**5 枚とも一致**した（ヘッダ helper 化と
  key 経路が画素を変えていないこと）。
- **詳細を持たない作品は、従来の `panels`（章ごとに 1 枚）の経路をそのまま通る。**
  後方互換を構造で保証する。`panel.detail` の無い型も同じ（`details` があっても key だけ）。
- 型を広げた後は、5 枚とも**意図的に変わる**。`dialogue-bust` を共有する
  `black-swan-ai` / `cyber-basics` も同じだけ人物と札が動く。**再焼きはしない**
  （焼けることは `--still` で確認）。
- 決定性: 同じ時刻の 2 回の描画が SHA-256 一致。`--start 560` の先頭フレームは
  同じ t の `--still` と一致（差はエンコードの YUV 変換ぶん。`--crf 0` でも
  mean 0.79 / 最頻は 0）。
- 通し焼き: **1280×720 / 30fps / 1033.79 秒 / AAC 44.1kHz stereo**、
  `export_timeline` の実尺警告 0。`scriptcheck --strict` は ok。

### 取り直した事実（サンプル『ハッブルの鏡』）

`research/sources.yaml` 16 件・`facts.yaml` 22 件・`notes/` 16 件・検索語 10 件。
主な訂正（`queries.md`）:

- STS-61 の総船外活動 **28.5 時間 → 35 時間 28 分**（ESA）。
- 軌道 **559km → 約 483km / 周期 約 95 分**（NASA Observatory）。
- 主鏡の表面 **10nm → 1µm 未満**（NASA は 10nm と書かない）。
- HDF の天域比較は **10 円玉ではなく硬貨**（75 フィート先）。
- ファーストライト **1990年5月20日**、不具合の公表 **1990年6月27日**。
- HDF: **1995年12月18–28日 / 342 露出 / 150 周の軌道を予定 / 4 フィルター /
  100 時間超 / 1,500 → 約 3,000 銀河 / 1996年1月15日公開**。

99.8% / 97% は記録ではなく**作品内の値**として `kind: in-work` に置いた。

### 足したもの・変えたもの

- 新規: `skills/guide-research/`、`schemas/research.schema.json`、
  `projects/hubble-mirror/research/`（README・queries・sources・facts・notes 16）、
  `review/compare/details/`（代表 10 枚）、`.claude/skills/guide-research`（symlink）。
- 変更: `engine/export_timeline.py`（`details` の解決と実尺警告）、
  `engine/layouts/dialogue_bust.py`（`_header` / `detail_geometry` / カードの
  切替と切り詰め）、`engine/scriptcheck.py`（詳細と研究の検査）、
  `references/templates/dialogue-bust/template.yaml`（`panel.detail` /
  `detail_fade` / 幅と位置）、`schemas/video.schema.json`（`details`）、
  `projects/hubble-mirror/video.yaml`（23 枚）、`README.md` / `docs/` / `skills/` /
  `install.sh` / `.claude-plugin/`（0.5.0・8 スキル）。
- 触っていない: `semantic-audio-loom/`、`distill-essence-engine/`、`script.yaml` /
  `台本.md` / `reading.yaml` / `bgm.yaml`、他の作品の再焼き。

## 0.4.0 — 2026-11-03 人物の個性と感情を、台本・声・絵の機構へ通した

0.3.0 の通しサンプル『ハッブルの鏡』は、事実と構成の評価は高かったが、148 cue の
表情はすべて neutral、速度は 2 語、聞き手は無反応だった。人物設定も 1 ファイルに
2 人ぶんが同居し、`role` / `wants` / `fears` / `speech` の 7 欄しかなかった。
今回はエンタメ性の焦点を**人物の差と感情**に置き、それを台本・声・表情・反応・
身体の全部へ通した。途中で、感情を強くするほど説明の意味が取れなくなることが
分かったので、**文学の評議会とは別に、読者が意味を持ち帰れるかだけを見る門**を
足した。採用は二つの門の両方を通った版だけで決める。

### 人物を一人 1 ファイルにした

`characters/<id>.character.yaml` が人物造形の正本。`id` は cast の id と一致する。

- 欄は `concept` / `role` / `background` / `wants` / `fears` / `contradiction` /
  `stance` / `habits` / `humor` / `speech` / `moves` / `arc` / `relationship` /
  `emotions` / `samples`。
- `emotions` は 6 つ以上。キーは自由（`pride` / `shame` / `awe` …）。
- `face` は cast の `expressions`、`voice` / `speed` / `volume` / `delivery` は
  SAL の語彙であることを `persona.py check` が見る。語彙は SAL の `PERF_ENUMS`
  から読む（写さない）。
- `persona.yaml` は `pair`（関係）だけへ痩せた。`characters[]` を埋め込んだ旧形式も
  読み込みの後方互換として読む。
- 解決は `engine/characters.py` に集約し、`persona.py` / `acting.py` /
  `scriptcheck.py` / `export_timeline.py` が同じ規則で読む。

### `beat` を演技の正本にした

`beat` は人物票の感情キーで、顔はそこから解決される。`face` を全 cue に写さない。

- `export_timeline.py` が `emotions.<beat>.face` を解決する。明示 `face` が優先。
  どちらも無ければ `cast.yaml` の `by_emotion[emotion]`、それも無ければ既定。
- `react.<id>.beat` も同じ規則。記号（`mark`）は 3 文字まで、全体で 8〜15 か所。
- `timeline.json` には**解決済み**の `face` と `react.<id>.face` が入る。
  絵を描く側は `beat` を推測しない（timeline が自己完結し、同じ時刻に同じ絵が出る）。
- 聞き手の顔は、自分の発話の頭と反応の頭を人物ごとの時刻列にほどき、`bisect` で引く。
  1 コマは状態を持たない。遅い方が勝ち、自分の発話が始まれば発話が優先。
- 記号は `cue.start + lead` からの経過時間だけで alpha / 拡大 / 位置を決める。
- `cast.yaml` の `motion_gain`（表情 → 倍率）が、解決済みの顔の身体の揺れに掛かる。
- 新スキル `skills/guide-acting/`。**書く前**に章ごとの感情の弧と人物ごとの
  「漏らす／隠す」を `review/acting/plan.md` に置き、**採用後**に cue へ欄を振る。

### 評議会を 10 次元にした

cast のいる作品は既存 8 次元 + `character-depth` + `character-role`。
**次元数の違う平均を混ぜない。** `review.py` に `compare --before --after`
（評価者 id の集合が同じときだけ差分表を出す）と `table --versions` を足した。

### 説明の門を足した（文学の評議会とは混ぜない）

**文学評議会の平均だけでは、解説動画のよしあしを測れない。** 情感の断片を高く評価する
評議会は、意味の取れない台本にも高い点を出す。そこで、読者が意味を持ち帰れるかだけを
見る門を、評議会とは**別の台帳**で足した。

- `engine/viewer.py` と `skills/guide-viewer/`。3 人の初見の読者を独立に招集し、
  明快さと、事実の復元（cause / fix / numbers / rejected / paper）を測る。
- 事実は 5 項目それぞれ 3 人中 2/3 以上の復元（yes=1、partial=0.5、no=0）で pass。
- 明快さのしきい値は**平文の基準の平均 − 10 点**。同じ事実を人物も感情も無しで
  書いた台本（`baseline-plain`）を先に測り、そこから引く。固定の点では、
  基準そのものが通らない。
- 説明設計の評価者を別に 1 体置き、75 点未満か `critical` があれば落とす。
- **採用は二つの門の両方**。評議会の平均 60 超と、この門の pass。平均には混ぜない。
- 記録は `projects/<作品>/review/viewers/<版>.yaml`。`scores.yaml` とは別ファイル。

台本の側にも規則を足した（`skills/guide-script/SKILL.md`）。**読点は文節の切れ目に
打つ。一語ずつ区切らない。** 説明の cue は 1 cue = 1 命題で、主語・述語・分母を
落とさない。情感の cue は断片でよい。`scriptcheck.py` が読点 3 つ以上・区切りの
平均 4 字以下を警告する（`--strict` で失敗）。

### サンプル『ハッブルの鏡』を作り直した

骨（5 章・事実の柱・百分率と紙）は保ち、人物の声と反応で振った。台詞の量は
v1 の約 1.4 倍（v6）、約 2.5 倍（v12）。**増えたぶんは説明の層**で、定義・分母・
因果を言い切る行が入った。尺は v1 の 398 秒から 1034 秒になった。

- v1 の採用本文を v1b として 10 次元で採り直し、v4 / v5 / v6 を**同じ 10 の
  評価者 id・各 10 本・独立**で評価した。**v6 は評議会で 76.00（v1b +6.70）を取り、
  いったん採用した。**
- ところが、足したばかりの門に v6 は落ちた（明快さ 41.00、原因・数字・紙の事実が
  2/3 に届かない）。**感情の層を強くするほど、説明の層が断片になり、意味が取れなく
  なっていた。** 台本を v7〜v12 で書き直した。v7〜v10 は固定 75 の旧しきい値で落ち、
  v11 でしきい値を平文の基準 − 10 に直した。
- v12 は、**説明の層と感情の層を分けて**書いた版。定義は主語・述語・分母まで言い切り、
  感情は短い行・間・反応で作る。評議会 70.60、門は pass（明快さ 64.00 / しきい値
  59.00、事実の最小 0.83、説明設計 88）。**二つの門を両方通った最後の版として
  v12 を採用した。**
- **v1b → v6**: 平均 69.30 → 76.00（**+6.70**）。`character-depth` 60 → 74（+14）、
  `character-role` 68 → 76（+8）、共通 8 次元 70.63 → 76.25（+5.62）。
- 演技の計測（`acting.py`）: v1 の beat 0% / 聞き手の顔 0% / 速度 2 語 /
  人物ごとの表情 0 種 → v12 の beat 100% / 解決済み face 100% / 聞き手の顔 90% /
  記号 8 か所 / 速度 5 語 / 人物ごとの表情 5 種。
- 309 cue / 5 章 / 1033.79 秒（17 分 14 秒）。1280×720 / 30 fps。章の頭は
  c001 / c043 / c085 / c190 / c236。字幕の 27 字制限に合わせ、長い行は文節の切れ目で
  割った。読みは `draft` のあと 46 か所を手で直した。

### 直した穴

| 見つけたこと | 原因 | 直した所 |
| --- | --- | --- |
| `FORCE=1` で組み立てが `unrecognized arguments: --force` で止まる | `make.sh` が `assemble.py` に `--force` を渡していた。SAL の受け口は `--retrim` | `make.sh` で `FORCE=1` を `--retrim` に写す |
| `……` だけの cue が声を持たず `scriptcheck.py` で落ちる | 台本を起こすとき、沈黙まで cue にしていた | v6 で 7 か所、v12 で 8 か所を cue にせず、次の cue の `pause_before` へ畳んだ（`guide-script` の既存規則） |
| 読みが旧 cue 名のまま | `script.yaml` を作り直したのに `reading.yaml` を引き継いだ | v6 で 215 cue、v12 で 309 cue を `draft` → 数字・`%`・Latin を手で直し、`audit --strict` を通した |
| 演技の監査が「明示 face 0%」で警告し続ける | 監査が明示 `face` だけを数え、`beat` の解決を見ていなかった | 監査も `characters.resolve_face` を使い、解決済みの顔と `react.beat` を数える |

### 決めたこと

- **顔は写さない。`beat` から解決する。** `docs/contract.md` の「`face` を必ず
  明示する」を改めた。timeline には解決済みを残すので、決定性は保たれる。
- **感情を名指ししない。** 間・聞き手の反応・表情・身体で作る。
- **まばたきはしない**（0.3.0 から据え置き）。

### 検算

| 確かめたこと | 結果 |
| --- | --- |
| `engine/acting.py audit --strict`（v12） | 309/309 cue、beat 100% / face 100% / 聞き手 90%、記号 8 か所、警告なし |
| `engine/scriptcheck.py --strict` / `reading.py audit --strict` | 309 cue / 5 章、エラーなし |
| `engine/persona.py check --cast mirai-mirabo` | ok（2 人） |
| `tools/check_layout.py` | 綴り・schemas とも ok |
| `review.py validate`（v1b / v4 / v5 / v6 / v12） | 各 10 本、すべて通過 |
| `review.py compare --before v1b --after v6` | +6.70（上記） |
| `viewer.py`（v12） | 明快さ 64.00 ≥ 59.00、事実 5 項目すべて pass、説明設計 88 |
| `ffprobe` | 1280×720 / 30 fps / 1033.794 秒 / h264 + aac |
| `--still 400.0` を 2 回 | SHA-256 が一致（決定性） |
| 実測の話速（timeline の cue 実尺） | v12 4.32 字/秒（v1 4.79、約 10% 遅い） |
| 章頭のチャイム（5 か所） | 各章の頭に打音の立ち上がり（-23〜-26 dB） |
| `compare/v1/` `compare/v6/` `compare/v12/` の 7 場面 | 表情・反応・記号の差が目で分かる |

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
