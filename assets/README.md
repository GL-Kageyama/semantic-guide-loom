# assets/

| ファイル | 何 | どこから |
| --- | --- | --- |
| `repo-hero.png` | README の頭の絵 | `projects/cyber-basics` の 29.0 秒のコマ |

**外で描いた絵ではない。** このリポジトリが焼く動画の、そのままの 1 コマである。
作り直すときは：

```bash
SKIP_VOICE=1 ./engine/make.sh projects/cyber-basics          # timeline.json を作る
<venv> engine/render.py --timeline build/cyber-basics/timeline.json \
    --still 29 --out assets/repo-hero.png
```

⚠️ `*.png` は Git LFS に載る（`.gitattributes`）。
