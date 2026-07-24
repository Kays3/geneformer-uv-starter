import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
START_SCRIPT = ROOT / "start.sh"
TMUX_CONFIG = ROOT / "config" / "tmux.conf"


def test_start_script_has_valid_bash_syntax() -> None:
    subprocess.run(["bash", "-n", START_SCRIPT], check=True)


def test_start_script_help_documents_remote_lifecycle() -> None:
    result = subprocess.run(
        [START_SCRIPT, "--help"],
        check=True,
        capture_output=True,
        text=True,
    )

    for command in ("remote", "remote-status", "remote-attach", "remote-stop"):
        assert command in result.stdout


def test_remote_server_binds_to_tailscale_ip_not_all_interfaces() -> None:
    script = START_SCRIPT.read_text(encoding="utf-8")

    assert '--ip "$tailscale_ip"' in script
    assert "--ip 0.0.0.0" not in script


def test_remote_tmux_uses_repository_config_and_isolated_socket() -> None:
    script = START_SCRIPT.read_text(encoding="utf-8")
    config = TMUX_CONFIG.read_text(encoding="utf-8")

    assert 'tmux -L "$tmux_socket" -f "$tmux_config"' in script
    assert "set-option -g mouse on" in config
    assert "set-option -g set-clipboard on" in config
    assert "copy-selection-and-cancel" in config
