"""The chat assistant runtime (a Node program from web/), started from Python."""

import shutil
import socket
import subprocess
from pathlib import Path

from brsr_p6.core.paths import WEB_DIR


RUNTIME_PORT = 8200        # web/server/runtime.ts listens here (its RUNTIME_PORT setting)


def port_in_use(port: int) -> bool:
    """True when something on this computer already listens on the port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.5)
        return probe.connect_ex(("127.0.0.1", port)) == 0


def start_runtime(web_dir: Path = WEB_DIR):
    """Start the CopilotKit runtime as a background program.  Returns (process or None, a message for the user)."""
    web_dir = Path(web_dir)
    if not (web_dir / "node_modules").is_dir():
        return None, "Assistant not started: run `npm install` in web/ first (see web/README.md)."
    if not (web_dir / ".env").is_file():
        return None, "Assistant not started: copy web/.env.example to web/.env and put your GOOGLE_API_KEY (a free Gemini key) in it."
    node = shutil.which("node")
    if node is None:
        return None, "Assistant not started: Node.js 20 or newer is not installed."
    if port_in_use(RUNTIME_PORT):                  # a run stopped with the red square can leave the old runtime behind
        return None, f"The assistant runtime is already running on port {RUNTIME_PORT} (left from an earlier run); using it."
    process = subprocess.Popen([node, "--env-file=.env", "--import", "tsx", "server/runtime.ts"], cwd=web_dir)
    return process, "Assistant runtime started."
