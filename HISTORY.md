# HISTORY

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
