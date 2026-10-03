#!/bin/bash
# Everything of yours that isn't on GitHub, in one file: .env, Ultron's memory, saved
# chats, scheduled jobs, school notes, images, 3D models, videos and uploads.
#   scripts/backup.sh                  writes ~/Ultron-backup-<date>.tgz
#   scripts/backup.sh restore FILE     puts a backup into this project (e.g. on a new Mac)
# The file holds your keys (.env): keep it to yourself.
# Not included: the image and video models (scripts/setup_images.sh and setup_video.sh
# download them again) and the log.
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"  # -P: the real path, as Claude Code sees it
STORAGE="backend/storage"
DATA=(.env "$STORAGE"/{chats.json,memory.json,jobs.json,school.md,homework_seen.json,usage.json,spotify_token.json}
  "$STORAGE"/{assets,models,uploads,videos})
# Saved chats continue a Claude Code conversation, which Claude Code keeps in a folder
# named after the storage folder's path (every other character becomes a dash).
SESSIONS="$HOME/.claude/projects/$(printf %s "$ROOT/$STORAGE" | sed 's/[^a-zA-Z0-9]/-/g')"

if [ "${1:-}" = restore ]; then
  FILE="${2:?Usage: scripts/backup.sh restore FILE}"
  tar -tzf "$FILE" >/dev/null  # a readable backup, before anything is replaced
  for f in "${DATA[@]}"; do
    if [ -f "$ROOT/$f" ]; then
      read -r -p "This replaces the .env, memory and chats already in $ROOT. Type yes to go on: " answer
      [ "$answer" = yes ] || exit 1
      break
    fi
  done
  tar -xzf "$FILE" -C "$ROOT" --exclude sessions
  if tar -tzf "$FILE" | grep -q '^sessions/'; then
    mkdir -p "$SESSIONS"
    tar -xzf "$FILE" -C "$SESSIONS" --strip-components 1 sessions
  fi
  echo "Restored into $ROOT. Restart Ultron if he's running."
  exit 0
fi

OUT="$HOME/Ultron-backup-$(date +%Y-%m-%d).tgz"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir "$TMP/sessions"
for f in "$SESSIONS"/*.jsonl; do
  [ -e "$f" ] || continue  # no conversations yet
  id="$(basename "$f" .jsonl)"
  if grep -qF "\"$id\"" "$ROOT/$STORAGE/chats.json" 2>/dev/null; then cp "$f" "$TMP/sessions/"; fi
done

HAVE=()
for f in "${DATA[@]}"; do
  if [ -e "$ROOT/$f" ]; then HAVE+=("$f"); fi
done

(umask 077 && tar -czf "$OUT" --exclude .DS_Store --exclude .gitkeep -C "$ROOT" "${HAVE[@]}" -C "$TMP" sessions)
echo "Saved $OUT ($(du -h "$OUT" | cut -f1)). It holds your keys: keep it to yourself."
