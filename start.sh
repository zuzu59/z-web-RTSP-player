#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
  printf 'Erreur : Python 3 est introuvable dans le PATH.\n' >&2
  exit 1
fi

if ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))'; then
  printf 'Erreur : Python 3.10 ou plus récent est requis.\n' >&2
  exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  printf 'Erreur : FFmpeg est introuvable dans le PATH.\n' >&2
  printf 'Installez FFmpeg puis relancez ce script.\n' >&2
  exit 1
fi

if [[ ! -f "$PROJECT_DIR/app.py" || ! -f "$PROJECT_DIR/index.html" ]]; then
  printf 'Erreur : app.py ou index.html est absent de %s.\n' \
    "$PROJECT_DIR" >&2
  exit 1
fi

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8089}"
export HOST PORT

cd "$PROJECT_DIR"
printf 'Démarrage de la visionneuse sur http://%s:%s\n' "$HOST" "$PORT"
exec python3 "$PROJECT_DIR/app.py"
