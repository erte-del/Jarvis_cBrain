#!/bin/bash
# One-time setup for image generation (the generate_image tool).
#   scripts/setup_images.sh
# Installs mflux in its own Python, downloads FLUX.2 Klein 4B from Hugging Face
# (~16 GB), saves an 8-bit copy for Apple Silicon, then deletes the download.
# Needs uv (https://docs.astral.sh/uv/). Safe to run again: finished steps are skipped.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FLUX="${JARVIS_FLUX_DIR:-$ROOT/backend/storage/flux}"
MODEL="$FLUX/flux2-klein-4b-q8"
PY="$FLUX/.venv/bin/python"

mkdir -p "$FLUX"
if [ ! -x "$PY" ]; then
  echo "== Installing mflux"
  uv venv --python 3.12 "$FLUX/.venv"
  uv pip install --python "$PY" mflux==0.20.0
fi

if [ ! -d "$MODEL" ]; then
  echo "== Downloading FLUX.2 Klein 4B (~16 GB) and saving an 8-bit copy"
  HF_HOME="$FLUX/hf" "$FLUX/.venv/bin/mflux-save" --model flux2-klein-4b --quantize 8 --path "$MODEL.tmp"
  mv "$MODEL.tmp" "$MODEL"
  rm -rf "$FLUX/hf"
fi

echo "== Image generation is ready. Restart Ultron to use it."
