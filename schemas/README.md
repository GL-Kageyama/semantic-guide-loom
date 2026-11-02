# schemas/ — 台本と型とキャストの形

配る YAML の形を JSON Schema で書き留めたもの。**実行時の検査ではない**
（`make.sh` はこれを見ない）。型やキャストを足すときに、欄を外していないかを
確かめるために置いてある。

| ファイル | 何の形か | 正本 |
| --- | --- | --- |
| `video.schema.json` | `video.yaml`（映像の台本） | `projects/<作品>/video.yaml` |
| `template.schema.json` | `template.yaml`（型＝絵の側） | `references/templates/<型>/template.yaml` |
| `cast.schema.json` | `cast.yaml`（誰が画面に居るか） | `characters/<キャスト>.cast.yaml` |
| `persona.schema.json` | `persona.yaml`（誰がどう話すか） | `characters/<キャスト>.persona.yaml` |
| `reading.schema.json` | `reading.yaml`（声に読ませる読み） | `projects/<作品>/reading.yaml` |
| `bgm.schema.json` | `bgm.yaml`（敷き音の意図とミックス） | `projects/<作品>/bgm.yaml` |

## `script.yaml` の形は、ここに無い

`script.yaml` は **semantic-audio-loom の scene 形式そのもの**である
（1 cue = 1 行 = 1 つの声）。形の正本は隣のリポジトリに在る。

- `semantic-audio-loom/schemas/scene.schema.json`

**ここへ写さない。** 写すと、向こうが欄を足したときに、こちらの写しが黙って
古くなる。このリポジトリは音の台本を読むだけで、形は決めない。

## 確かめ方

```bash
<venv> - <<'PY'
import json, sys, yaml, glob
from jsonschema import Draft202012Validator
def check(schema_path, glob_pat):
    v = Draft202012Validator(json.load(open(schema_path)))
    for p in glob.glob(glob_pat, recursive=True):
        v.validate(yaml.safe_load(open(p)))
        print("ok", p)
check("schemas/video.schema.json",    "projects/*/video.yaml")
check("schemas/template.schema.json", "references/templates/*/template.yaml")
check("schemas/cast.schema.json",     "characters/*.cast.yaml")
check("schemas/persona.schema.json",  "characters/*.persona.yaml")
check("schemas/reading.schema.json",  "projects/*/reading.yaml")
check("schemas/bgm.schema.json",      "projects/*/bgm.yaml")
PY
```

`tools/check_layout.py` が上の 6 つをまとめて走らせる。

## 欄を足すとき

- **`additionalProperties: true` が既定。** 型が読む欄は型ごとに違うので、
  知らない欄を弾かない（`dialogue-bust` の `term` / `key` と、`narrate-slide` の
  `bullets` が同じ `chapters` に同居している）。
- **必須（`required`）は「無いと焼けないもの」だけ。** 好みの欄を必須にしない。
