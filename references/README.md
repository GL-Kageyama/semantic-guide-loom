# references/ — 型と表情シート

絵の側の資材。**意味を持たないもの**がここに集まる。

| 置き場 | 何 | 誰が読むか |
| --- | --- | --- |
| `templates/<型>/template.yaml` | 型の「数」（画布・色・書体・位置・間合い） | `engine/render.py`（と `export_timeline.py` が `chapter_lead` だけ） |
| `sheets/*.png` | 表情シート（4列×2行の 8 マス・背景透過） | `engine/prepare_assets.py` |

## templates/

型は 2 つの部品からなる。ここに在るのは**数の側**だけで、**並べ方**は
`engine/layouts/<layout>.py` に在る（`template.yaml` の `layout:` が名乗る）。

色違い・位置違いの型は YAML を 1 枚足すだけで済む。並べ方が違う型は
モジュールを 1 本足す。手順と欄の一覧は [../docs/template-contract.md](../docs/template-contract.md)、
形は [../schemas/template.schema.json](../schemas/template.schema.json)。

**型は作品を知らない。** 特定の題・人数・章の数を型に書かない。

## sheets/

切り抜きの元。`prepare_assets.py` が口の 3 状態と 8 表情をここから作る。

**配布物に入れている**（Git LFS）。理由と、差し替えたときの測り直し方は
[sheets/README.md](sheets/README.md)。

## ここに無いもの

- **声・効果音・BGM** … 作品ごとの入力。`projects/<作品>/assets/`（Git LFS）。
- **台本** … 作品が持つ。`projects/<作品>/script.yaml`（音）と `video.yaml`（絵）。
- **キャスト** … `characters/<名前>.cast.yaml`（画面）と `persona.yaml`（言葉）。
