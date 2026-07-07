#!/usr/bin/env python3
"""
WhatsApp Job Fetcher
=====================
Manages the whatsapp_server.js Node.js bridge process and exposes a clean
Python API used by app.py.

The Node server runs on localhost:8765 and persists across Streamlit reruns.
"""

import os
import shutil
import subprocess
import time
import requests

SERVER_PORT = 8765
SERVER_URL = f"http://127.0.0.1:{SERVER_PORT}"
SERVER_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whatsapp_server.js")
NODE_MODULES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "node_modules")

# Resolve node binary — Streamlit subprocesses don't inherit nvm PATH
def _find_node() -> str:
    # 1. Already on PATH (plain installs, Homebrew)
    found = shutil.which("node")
    if found:
        return found
    # 2. Common nvm location
    nvm_node = os.path.expanduser("~/.nvm/versions/node")
    if os.path.isdir(nvm_node):
        versions = sorted(os.listdir(nvm_node), reverse=True)
        for v in versions:
            candidate = os.path.join(nvm_node, v, "bin", "node")
            if os.path.isfile(candidate):
                return candidate
    # 3. Homebrew default
    for p in ["/usr/local/bin/node", "/opt/homebrew/bin/node"]:
        if os.path.isfile(p):
            return p
    raise RuntimeError("Node.js not found. Install it via nvm or Homebrew.")

NODE_BIN = _find_node()

_server_proc = None  # module-level so it survives Streamlit reruns within the same process


def _is_server_running() -> bool:
    try:
        r = requests.get(f"{SERVER_URL}/status", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def ensure_server_running() -> bool:
    """Start the Node.js bridge if it's not already up. Returns True if running."""
    global _server_proc
    if _is_server_running():
        return True

    env = os.environ.copy()
    env["NODE_PATH"] = NODE_MODULES

    _server_proc = subprocess.Popen(
        [NODE_BIN, SERVER_SCRIPT],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
        cwd=os.path.dirname(SERVER_SCRIPT),
    )

    for _ in range(20):          # wait up to ~10 s for the server to come up
        time.sleep(0.5)
        if _is_server_running():
            return True

    return False


def get_status() -> dict:
    """Returns { status: str, qr: str|None }"""
    try:
        return requests.get(f"{SERVER_URL}/status", timeout=5).json()
    except Exception as e:
        return {"status": "error", "qr": None, "error": str(e)}


def connect() -> dict:
    """Tell the server to initialise the WhatsApp client."""
    try:
        return requests.get(f"{SERVER_URL}/connect", timeout=10).json()
    except Exception as e:
        return {"status": "error", "error": str(e)}


def list_groups() -> list[dict]:
    """Returns [{ id, name, participants }] sorted by name."""
    try:
        r = requests.get(f"{SERVER_URL}/groups", timeout=60)
        if r.status_code == 503 and r.json().get("error") == "DETACHED_FRAME":
            raise RuntimeError("DETACHED_FRAME")
        r.raise_for_status()
        return r.json()
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Could not load groups: {e}") from e


def fetch_messages(chat_id: str, limit: int = 200) -> list[dict]:
    """
    Returns list of dicts compatible with the jobs_to_excel / render_job_cards
    format expected by app.py.
    """
    try:
        r = requests.get(
            f"{SERVER_URL}/messages",
            params={"chat_id": chat_id, "limit": limit},
            timeout=60,
        )
        r.raise_for_status()
        raw = r.json()
    except Exception as e:
        raise RuntimeError(f"Message fetch failed: {e}") from e

    jobs = []
    for m in raw:
        body = m.get("body", "")
        title = body.split("\n", 1)[0].strip()
        jobs.append({
            "message_id": m.get("id", ""),
            "title": title,
            "company": m.get("author", ""),
            "location": "",
            "job_type": "",
            "description": body,
            "requirements": "",
            "date_posted": m.get("date_str", ""),
            "date_ts": m.get("timestamp", 0),
            "sender": m.get("author", ""),
            "source_url": m.get("source_url", ""),
        })

    return jobs


def disconnect() -> dict:
    """Logout from WhatsApp and destroy the client session."""
    try:
        return requests.post(f"{SERVER_URL}/disconnect", timeout=15).json()
    except Exception as e:
        return {"status": "error", "error": str(e)}
