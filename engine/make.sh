#!/usr/bin/env bash
# 1 本ぶんの解説動画を、素材から書き出しまで通す。
#
#   ./engine/make.sh projects/cyber-basics
#   ./engine/make.sh projects/cyber-basics --still 40     # 1 枚だけ出す
#
# 環境変数:
#   FORCE=1        声を作り直す（参照や voice_fx を変えたときはこれが要る）
#   SKIP_ASSETS=1  表情シートの切り出しを飛ばす
#   SKIP_VOICE=1   声の生成を飛ばす（台本を変えていないとき）
#   BGM=auto       敷き音を作り直すか（auto=入力が変わったときだけ / force・1=毎回 / 0=飛ばす）
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
# 資材（声・効果音・BGM）が作品の隣に在れば、それを読む。無ければ build/ に作る。
# projects/<作品>/assets/ の中で作られる派生（voice_trim・renders・*_tiled.wav）は .gitignore。
if [ -d "$WORK/assets" ]; then AUDIO="$WORK/assets"; else AUDIO="$BUILD/audio"; fi

[ -f "$WORK/script.yaml" ] || { echo "script.yaml が無い: $WORK" >&2; exit 2; }
[ -d "$SAL" ] || { echo "semantic-audio-loom が無い: $SAL" >&2; exit 2; }

mkdir -p "$BUILD" "$AUDIO" "$WORK/renders"

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

# 読み（reading.yaml）があるときは、build/<作品>/ に「line を読みへ差し替えた」舞台を作り、
# 声・組み立て・時刻はその舞台を読む。作品のファイルは書き換えない。
SCRIPT_DIR="$WORK"
if [ -f "$WORK/reading.yaml" ]; then
  PRUNE_FLAG=()
  # 声を作らない回に消すと、古い声が無いまま混ざる。声を作る回だけ捨てる。
  [ "${SKIP_VOICE:-0}" != "1" ] && PRUNE_FLAG=(--prune-voice)
  step "2/5 声（読みの舞台 → 1 キュー 1 ファイル）"
  run "$PY" "$ROOT/engine/reading.py" stage --project "$WORK" --stage "$BUILD" \
      --assets "$AUDIO" "${PRUNE_FLAG[@]+"${PRUNE_FLAG[@]}"}"
  SCRIPT_DIR="$BUILD"
else
  step "2/5 声（1 キュー 1 ファイル）"
fi
if [ "${SKIP_VOICE:-0}" != "1" ]; then
  run env PYTHONPATH="$SAL" "$PY" "$SAL/projects/longform/explainer/build_voice.py" \
      --dir "$SCRIPT_DIR" --assets "$AUDIO" "${FORCE_FLAG[@]+"${FORCE_FLAG[@]}"}"
fi

BGM_MODE="${BGM:-auto}"
HAS_BGM=0
[ -f "$WORK/bgm.yaml" ] && HAS_BGM=1
USE_BGM=0
[ "$HAS_BGM" = "1" ] && [ "$BGM_MODE" != "0" ] && USE_BGM=1

if [ "$USE_BGM" = "1" ]; then
  step "3/5 組み立て（BGM → 間・声量・章の印 → 1 本の WAV）"
  BGM_FORCE_FLAG=()
  case "$BGM_MODE" in force|1) BGM_FORCE_FLAG=(--force) ;; esac
  run "$PY" "$ROOT/engine/bgm.py" generate --project "$WORK" --assets "$AUDIO" \
      "${BGM_FORCE_FLAG[@]+"${BGM_FORCE_FLAG[@]}"}"
  # mix は下で 1 回だけ。ここでは mix.yaml を書かせ、混ぜない。
  run env PYTHONPATH="$SAL" "$PY" "$SAL/projects/longform/assemble.py" \
      --dir "$SCRIPT_DIR" --assets "$AUDIO" --no-render "${FORCE_FLAG[@]+"${FORCE_FLAG[@]}"}"
  run "$PY" "$ROOT/engine/bgm.py" mix --project "$WORK" --stage "$SCRIPT_DIR" --assets "$AUDIO"
else
  step "3/5 組み立て（間・声量・章の印 → 1 本の WAV）"
  run env PYTHONPATH="$SAL" "$PY" "$SAL/projects/longform/assemble.py" \
      --dir "$SCRIPT_DIR" --assets "$AUDIO" "${FORCE_FLAG[@]+"${FORCE_FLAG[@]}"}"
fi

step "4/5 時刻（mix.yaml の実尺 → timeline.json）"
run "$PY" "$ROOT/engine/export_timeline.py" --project "$SCRIPT_DIR" \
    --out "$BUILD/timeline.json" --audio "$AUDIO/renders/$NAME.wav"

step "5/5 描画"
if [ "${1:-}" = "--still" ]; then
  run "$PY" "$ROOT/engine/render.py" --timeline "$BUILD/timeline.json" "$@"
else
  run "$PY" "$ROOT/engine/render.py" --timeline "$BUILD/timeline.json" \
      --out "$WORK/renders/$NAME.mp4" "$@"
  echo
  echo "できた: $WORK/renders/$NAME.mp4"
fi
