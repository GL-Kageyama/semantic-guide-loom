# 置き場 — 何をどこへ置くか

**入れるのは「入力」と「成果物」、入れないのは「中間物」。** これが置き場の唯一の規則。
入力は元へ戻せないもの、成果物は clone した人がそのまま見られるもの、中間物は
焼き直せば戻るもの。

## 何を、どこで決めるか

| 決めること | どこで決めるか |
| --- | --- |
| 何を言ってよいか（検証済みの事実） | `research/`（出典・抜き書き・`facts.yaml`） |
| 何を、どの順で話すか | `design.md` → `script.yaml` × `video.yaml` |
| 誰が声を出し、どう演じるか | `script.yaml` の `character` と演技の欄 |
| その人物が何を欲し、何を怖れるか | `characters/<id>.character.yaml` |
| 二人がどう噛み合うか | `characters/<名前>.persona.yaml` |
| 誰が画面に居るか | `characters/<名前>.cast.yaml` |
| 表情・聞き手の反応・身体の揺れ | cue の `face` / `react` と cast の `motion_gain` |
| 声にどう読ませるか | `reading.yaml`。字幕は `video.yaml` の `display` |
| 敷き音 | `bgm.yaml` → `assets/bgm/underlay.wav` |
| どう見えるか（色・位置・間合い） | `references/templates/<型>/` × `engine/layouts/` |
| 時刻 | **音の実尺**。台本から数え直さない |

## 作品の中

```
projects/<作品名>/
  design.md       題材・約束・章・事実の柱・説明の鎖（任意。設計から作るとき）
  reading.yaml    cue → 声に読ませる読み（任意。無ければ line をそのまま読む）
  bgm.yaml        敷き音の意図とミックス（任意。無ければ BGM の段を飛ばす）
  script.yaml     何を、どの順で、誰が、どう話すか（音の台本）
  video.yaml      題・章・字幕の表記・型・キャスト（映像の台本。詳細カードは details）
  chapters.yaml   章の頭の cue（音のチャイム）
  voice_fx.yaml   声に掛ける効果（任意）
  research/       調査の台帳（任意。出典・抜き書き・検証済みの事実）
    README.md     この作品の調査の目的・範囲・更新の仕方
    queries.md    検索語と訂正の記録
    sources.yaml  出典
    notes/        出典ごとの抜き書き
    facts.yaml    映像に使う事実（details[].fact が引く）
  review/         台本の版・評価・採用の記録（任意。設計から作るとき）
    acting/       感情の弧（plan.md）と版ごとの演技の計測（vN.yaml）
    viewers/      初見復元テストと説明の評価（vN/ と vN.yaml）
  assets/
    voice/        1 行 1 つの声（+ .params.yaml）— 入力
    sfx/  bgm/    効果音・敷き音 — 入力
  renders/        焼いた動画 — 成果物（Git LFS）
```

`assets/` の中で `assemble.py` が作る `voice_trim/` `voice_fx/` `renders/`
`*_tiled.wav` `*_short.wav` と、毎回書き直される `mix.yaml` は派生ゆえ `.gitignore`。
**作品の `renders/`（動画）とは別の置き場**であることに注意——`assets/renders/` は
組み立てた WAV（中間物）、`renders/` は焼いた MP4（成果物）。

## リポジトリの中

```
references/templates/<型>/template.yaml   型（配布する）
references/sheets/                        表情シート（入力。Git LFS）
characters/<キャスト>.cast.yaml            キャスト・画面（配布する）
characters/<id>.character.yaml             人物票・一人 1 ファイル（配布する）
characters/<キャスト>.persona.yaml         キャストの関係（配布する）
schemas/                                  ファイルの形（JSON Schema）
docs/                                     契約と手順
tools/check_layout.py                     置き場の綴りと schemas の検査
skills/
  semantic-guide-loom/SKILL.md            入口。焼く手順
  guide-research/ guide-design/ guide-cast/ guide-script/ guide-viewer/
  guide-acting/ guide-reading/ guide-bgm/ 判断が要る工程
engine/
  make.sh                                 5 段を通す
  prepare_assets.py characters.py persona.py acting.py sal_enums.py
  review.py viewer.py reading.py scriptcheck.py bgm.py
  export_timeline.py render.py common.py
  layouts/                                型の並べ方（dialogue_bust / narrate_slide）
build/<作品>/                              中間物（assets, audio, 読みの舞台, timeline.json）
                                          — .gitignore
assets/repo-hero.png                      README の絵（Git LFS）
```

`build/` は焼き直せば戻るので入れない。**表情シートも声も入力**（切り抜きからも、
声からも元には戻せない）、**`renders/` は成果物**（clone した人がそのまま見られる）。

**演技の計測は `review/acting/` に置く。** `review/reports/` は評価者の JSON だけの
場所で、`review.py` はそこの全 `*.json` を評価者として数える。YAML の計測を混ぜると
平均が壊れる（[review.md](review.md)）。

## 作品はリポジトリの外に置いてよい

`make.sh` は `script.yaml` と `video.yaml` のあるディレクトリならどこでも指せる。
その場合、音の資材は `projects/<作品>/assets/` が無ければ `build/<作品>/audio` に
作られ、動画は作品の `renders/` へ出る。

## Git と LFS

**音声と画像は Git LFS に入る**——`*.wav` `*.mp3` `*.m4a` `*.flac` `*.ogg` `*.mp4`
`*.png` `*.jpg` `*.jpeg`（規則は [`.gitattributes`](../.gitattributes)）。コミットされる
のは小さなテキストのポインタで、実体は GitHub 上の**このリポジトリの LFS ストレージ**に
ある。

**テキスト（コード・YAML・Markdown・TSV・JSON）は対象外**で、普通の blob として入る。

LFS に入るのは次の 3 つだけ。**どれも消さない。**

| 置き場 | 何 | なぜ入れるか |
| --- | --- | --- |
| `references/sheets/` | 表情シート | 切り抜きからは戻せない（入力） |
| `projects/*/assets/{voice,sfx,bgm}/` | 声・効果音・敷き音の原盤 | モデルを起こさないと戻らない（入力） |
| `projects/*/renders/*.mp4` | 焼いた動画 | clone した人がそのまま見られる（成果物） |

⚠️ `git-lfs` の無い clone は実体ではなくポインタを降ろす。clone の前に `git-lfs` を
入れ、後なら `git lfs pull` を走らせる。
⚠️ LFS はリポジトリとは別に計量され、所有者のアカウントに計上される。

## 置き場を移したら

```bash
python3 tools/check_layout.py
```

古い綴りが文書・コードに残っていないか、`schemas/` が実物に通るかを見る。
