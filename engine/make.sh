#!/usr/bin/env bash
# 1 本ぶんの解説動画を、素材から書き出しまで通す。
#
#   ./engine/make.sh works/cyber-basics
#   ./engine/make.sh works/cyber-basics --still 40     # 1 枚だけ出す
#
# 環境変数:
#   FORCE=1        声を作り直す（参照や voice_fx を変えたときはこれが要る）
#   SKIP_ASSETS=1  表情シートの切り出しを飛ばす
#   SKIP_VOICE=1   声の生成を飛ばす（台本を変えていないとき）
#   PY=…           venv の python（既定は $HOME/sonic-loom-spike/venv_tsukasa）
#   SAL=…          音の道具箱（既定は隣の semantic-audio-loom）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${PY:-$HOME/sonic-loom-spike/venv_tsukasa/bin/python}"
SAL="${SAL:-$ROOT/../semantic-audio-loom}"

[ $# -ge 1 ] || { echo "使い方: $0 <作品の置き場> [--still 秒]" >&2; exit 2; }
WORK_IN="$1"; shift
WORK="$(cd "$WORK_IN" && pwd)"
NAME="$(basename "$WORK")"
BUILD="$ROOT/build/$NAME"
AUDIO="$BUILD/audio"

[ -f "$WORK/script.yaml" ] || { echo "script.yaml が無い: $WORK" >&2; exit 2; }
[ -d "$SAL" ] || { echo "semantic-audio-loom が無い: $SAL" >&2; exit 2; }

mkdir -p "$BUILD" "$AUDIO" "$ROOT/out"

step() { printf '\n\033[1m── %s\033[0m\n' "$1"; }
run()  { echo "+ $*"; "$@"; }

FORCE_FLAG=()
[ "${FORCE:-0}" = "1" ] && FORCE_FLAG=(--force)

# キャストを名乗らない型（人物を置かない型）は、素材の段を飛ばす。
CAST="$("$PY" -c 'import sys,yaml;print((yaml.safe_load(open(sys.argv[1])) or {}).get("cast","") or "")' "$WORK/video.yaml")"

if [ "${SKIP_ASSETS:-0}" != "1" ] && [ -n "$CAST" ]; then
  step "1/5 素材（表情シート → 口の 3 状態）"
  run "$PY" "$ROOT/engine/prepare_assets.py" --work "$WORK" --out "$BUILD/assets"
fi

if [ "${SKIP_VOICE:-0}" != "1" ]; then
  step "2/5 声（1 キュー 1 ファイル）"
  run env PYTHONPATH="$SAL" "$PY" "$SAL/projects/longform/explainer/build_voice.py" \
      --dir "$WORK" --assets "$AUDIO" "${FORCE_FLAG[@]+"${FORCE_FLAG[@]}"}"
fi

step "3/5 組み立て（間・声量・章の印 → 1 本の WAV）"
run env PYTHONPATH="$SAL" "$PY" "$SAL/projects/longform/assemble.py" \
    --dir "$WORK" --assets "$AUDIO" "${FORCE_FLAG[@]+"${FORCE_FLAG[@]}"}"

step "4/5 時刻（mix.yaml の実尺 → timeline.json）"
run "$PY" "$ROOT/engine/export_timeline.py" --project "$WORK" \
    --out "$BUILD/timeline.json" --audio "$AUDIO/renders/$NAME.wav"

step "5/5 描画"
if [ "${1:-}" = "--still" ]; then
  run "$PY" "$ROOT/engine/render.py" --timeline "$BUILD/timeline.json" "$@"
else
  run "$PY" "$ROOT/engine/render.py" --timeline "$BUILD/timeline.json" \
      --out "$ROOT/out/$NAME.mp4" "$@"
  echo
  echo "できた: $ROOT/out/$NAME.mp4"
fi
