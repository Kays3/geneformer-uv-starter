#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Usage: ./start.sh [COMMAND]

Commands:
  (none)          Start JupyterLab in the foreground for local use
  check           Validate the Geneformer environment
  remote          Start JupyterLab on the Tailscale IP in a detached tmux session
  remote-status   Show the remote session and recent JupyterLab output
  remote-attach   Attach to the remote tmux session (detach with Ctrl-b d)
  remote-stop     Stop the remote tmux session
EOF
  exit 0
fi

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
analysis_root="$repository_root/geneformer-workspace/analysis"
tmux_session="${GENEFORMER_TMUX_SESSION:-geneformer-jupyter}"
tmux_socket="${GENEFORMER_TMUX_SOCKET:-geneformer}"
tmux_config="$repository_root/config/tmux.conf"

if [[ ! -f "$analysis_root/uv.lock" ]]; then
  if [[ -d "$repository_root/.geneformer-workspace" ]]; then
    echo "Run ./setup.sh once to move the legacy hidden workspace to geneformer-workspace/." >&2
    exit 1
  fi
  echo "Geneformer is not set up yet. Run ./setup.sh first." >&2
  exit 1
fi

cd "$analysis_root"

case "${1:-lab}" in
  check)
    exec uv run --locked --managed-python python scripts/smoke_test.py \
      --geneformer-root ../Geneformer
    ;;
  remote)
    if ! command -v tailscale >/dev/null 2>&1; then
      echo "Tailscale is not installed. Follow docs/machine-setup.md, then rerun." >&2
      exit 1
    fi
    if ! command -v tmux >/dev/null 2>&1; then
      echo "tmux is not installed. Run: sudo apt-get install -y tmux" >&2
      exit 1
    fi
    tmux_command=(tmux -L "$tmux_socket" -f "$tmux_config")
    tailscale_ip="$(tailscale ip -4 2>/dev/null | head -n 1)"
    if [[ -z "$tailscale_ip" ]]; then
      echo "Tailscale is not connected. Run: sudo tailscale up" >&2
      exit 1
    fi
    if "${tmux_command[@]}" has-session -t "$tmux_session" 2>/dev/null; then
      echo "Remote JupyterLab is already running in tmux session: $tmux_session"
    else
      printf -v remote_command 'exec %q _remote-server %q' \
        "$repository_root/start.sh" "$tailscale_ip"
      "${tmux_command[@]}" new-session -d -s "$tmux_session" "$remote_command"
      echo "Started remote JupyterLab in tmux session: $tmux_session"
    fi
    echo "Initial Tailscale address: http://$tailscale_ip:8888"
    echo "Get the token URL with: ./start.sh remote-status"
    echo "Attach with:            ./start.sh remote-attach"
    ;;
  remote-status)
    tmux_command=(tmux -L "$tmux_socket" -f "$tmux_config")
    if ! command -v tmux >/dev/null 2>&1 \
      || ! "${tmux_command[@]}" has-session -t "$tmux_session" 2>/dev/null; then
      echo "Remote JupyterLab is not running. Start it with: ./start.sh remote" >&2
      exit 1
    fi
    echo "tmux session: $tmux_session"
    "${tmux_command[@]}" capture-pane -p -J -t "$tmux_session" -S -80
    ;;
  remote-attach)
    tmux_command=(tmux -L "$tmux_socket" -f "$tmux_config")
    if ! command -v tmux >/dev/null 2>&1 \
      || ! "${tmux_command[@]}" has-session -t "$tmux_session" 2>/dev/null; then
      echo "Remote JupyterLab is not running. Start it with: ./start.sh remote" >&2
      exit 1
    fi
    exec "${tmux_command[@]}" attach-session -t "$tmux_session"
    ;;
  remote-stop)
    tmux_command=(tmux -L "$tmux_socket" -f "$tmux_config")
    if command -v tmux >/dev/null 2>&1 \
      && "${tmux_command[@]}" has-session -t "$tmux_session" 2>/dev/null; then
      "${tmux_command[@]}" kill-session -t "$tmux_session"
      echo "Stopped remote JupyterLab session: $tmux_session"
    else
      echo "Remote JupyterLab is not running."
    fi
    ;;
  _remote-server)
    tailscale_ip="${2:-}"
    if [[ -z "$tailscale_ip" ]]; then
      echo "Internal error: missing Tailscale IP." >&2
      exit 2
    fi
    echo "Starting JupyterLab on Tailscale IP $tailscale_ip."
    echo "Detach from tmux with Ctrl-b d; do not stop it with Ctrl-c."
    exec uv run --locked --managed-python jupyter lab \
      --no-browser \
      --ip "$tailscale_ip" \
      --port 8888 \
      --ServerApp.port_retries=10 \
      --ServerApp.allow_remote_access=True
    ;;
  lab)
    echo "Starting JupyterLab. Stop it with Ctrl+C."
    exec uv run --locked --managed-python jupyter lab
    ;;
  *)
    echo "Unknown command: $1" >&2
    echo "Run ./start.sh --help for available commands." >&2
    exit 2
    ;;
esac
