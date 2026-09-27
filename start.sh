#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="${RUNTIME_DIR:-$PROJECT_DIR/.runtime}"
PID_FILE="$RUNTIME_DIR/server.pid"
LOG_FILE="$RUNTIME_DIR/server.log"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8089}"

usage() {
  cat <<'EOF'
Usage: ./start.sh [start|stop|restart|status]

  start    Start the web server in the background (default).
  stop     Stop the server started by this script.
  restart  Restart the background server.
  status   Show whether the background server is running.

HOST and PORT configure the listener. Defaults: 0.0.0.0 and 8089.
RUNTIME_DIR optionally changes the directory for the PID and log files.
EOF
}

valid_pid() {
  [[ "${1:-}" =~ ^[1-9][0-9]*$ ]]
}

process_matches() {
  local pid="$1"
  local command_line
  valid_pid "$pid" || return 1
  kill -0 "$pid" 2>/dev/null || return 1
  command_line="$(ps -p "$pid" -o args= 2>/dev/null || true)"
  [[ "$command_line" == *"$PROJECT_DIR/app.py"* ]]
}

stored_pid() {
  [[ -f "$PID_FILE" ]] || return 1
  local pid
  pid="$(<"$PID_FILE")"
  valid_pid "$pid" || return 1
  printf '%s\n' "$pid"
}

start_server() {
  if [[ ! -x "$(command -v python3 || true)" ]]; then
    printf 'Erreur : Python 3 est introuvable dans le PATH.\n' >&2
    return 1
  fi

  if ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))'; then
    printf 'Erreur : Python 3.10 ou plus récent est requis.\n' >&2
    return 1
  fi

  if ! command -v ffmpeg >/dev/null 2>&1; then
    printf 'Erreur : FFmpeg est introuvable dans le PATH.\n' >&2
    printf 'Installez FFmpeg puis relancez ce script.\n' >&2
    return 1
  fi

  if [[ ! -f "$PROJECT_DIR/app.py" || ! -f "$PROJECT_DIR/index.html" ]]; then
    printf 'Erreur : app.py ou index.html est absent de %s.\n' \
      "$PROJECT_DIR" >&2
    return 1
  fi

  if pid="$(stored_pid)" && process_matches "$pid"; then
    printf 'Le serveur tourne déjà (PID %s) sur http://%s:%s\n' \
      "$pid" "$HOST" "$PORT"
    printf 'Journal : %s\n' "$LOG_FILE"
    return 0
  fi

  umask 077
  mkdir -p "$RUNTIME_DIR"
  rm -f "$PID_FILE"

  HOST="$HOST" PORT="$PORT" nohup python3 -u "$PROJECT_DIR/app.py" \
    >>"$LOG_FILE" 2>&1 </dev/null &
  local pid=$!
  printf '%s\n' "$pid" > "$PID_FILE"

  for _ in {1..10}; do
    if ! process_matches "$pid"; then
      rm -f "$PID_FILE"
      printf 'Erreur : le serveur n’a pas démarré.\n' >&2
      printf 'Dernières lignes du journal :\n' >&2
      tail -n 20 "$LOG_FILE" >&2 || true
      return 1
    fi
    sleep 0.2
  done

  printf 'Serveur démarré en arrière-plan (PID %s).\n' "$pid"
  printf 'Adresse : http://%s:%s\n' "$HOST" "$PORT"
  printf 'Journal : %s\n' "$LOG_FILE"
  printf 'Arrêt : %s stop\n' "$0"
}

stop_server() {
  local pid
  if ! pid="$(stored_pid)"; then
    printf 'Aucun PID valide trouvé dans %s.\n' "$PID_FILE"
    return 0
  fi

  if ! process_matches "$pid"; then
    rm -f "$PID_FILE"
    printf 'Le serveur ne tourne pas; ancien fichier PID supprimé.\n'
    return 0
  fi

  kill -TERM "$pid"
  for _ in {1..25}; do
    if ! kill -0 "$pid" 2>/dev/null; then
      rm -f "$PID_FILE"
      printf 'Serveur arrêté (PID %s).\n' "$pid"
      return 0
    fi
    sleep 0.2
  done

  printf 'Le serveur ne s’est pas arrêté à temps (PID %s).\n' "$pid" >&2
  return 1
}

show_status() {
  local pid
  if pid="$(stored_pid)" && process_matches "$pid"; then
    printf 'Serveur actif (PID %s). Journal : %s\n' "$pid" "$LOG_FILE"
  else
    printf 'Serveur arrêté.\n'
  fi
}

case "${1:-start}" in
  start) start_server ;;
  stop) stop_server ;;
  restart) stop_server && start_server ;;
  status) show_status ;;
  -h|--help|help) usage ;;
  *) usage >&2; exit 2 ;;
esac
