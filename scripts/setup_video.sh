#!/bin/bash
# One-time setup for video generation (the generate_video tool).
#   scripts/setup_video.sh
# Installs mlx-video in its own Python, downloads Wan 2.1 T2V 1.3B from Hugging Face
# (~17.6 GB), converts it for Apple Silicon, then deletes the download.
# Needs uv (https://docs.astral.sh/uv/). Safe to run again: finished steps are skipped.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WAN="${JARVIS_WAN_DIR:-$ROOT/backend/storage/wan}"
MLX_VIDEO="git+https://github.com/Blaizzy/mlx-video.git@87db56a51758fefb748a359b90a5283bb8ba4837"
RAW="$WAN/Wan2.1-T2V-1.3B"
MODEL="$WAN/Wan2.1-T2V-1.3B-MLX"
PY="$WAN/.venv/bin/python"

mkdir -p "$WAN"
if [ ! -x "$PY" ]; then
  echo "== Installing mlx-video"
  uv venv --python 3.12 "$WAN/.venv"
  # torch is only needed to convert the weights.
  uv pip install --python "$PY" "$MLX_VIDEO" torch
fi

if [ ! -f "$MODEL/config.json" ]; then
  echo "== Downloading Wan 2.1 T2V 1.3B (~17.6 GB)"
  "$PY" -c "from huggingface_hub import snapshot_download as d; d('Wan-AI/Wan2.1-T2V-1.3B', local_dir='$RAW')"
  echo "== Converting for MLX"
  "$PY" -m mlx_video.models.wan_2.convert --checkpoint-dir "$RAW" --output-dir "$MODEL"
  rm -rf "$RAW"
fi

echo "== Video generation is ready. Restart Jarvis to use it."
