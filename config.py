"""Configuration management: keyring for secrets, config.json for the rest."""
from __future__ import annotations

import json
import os
from typing import Any

import keyring

# ── Constants ─────────────────────────────────────────────────────────────────

_HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(_HERE, "config.json")

KEYRING_SERVICE = "auto-doc-workflow"
KEYRING_GITHUB = "github-token"

DEFAULTS: dict[str, Any] = {
    "repo_url": "",
    "ollama_model": "llama3.2",
    "n8n_port": 5678,
    "n8n_api_key": "",
    "github_webhook_id": "",
    "docker_compose_dir": _HERE,
}

# ── Public API ────────────────────────────────────────────────────────────────


def load_config() -> dict:
    """Load config.json, merging missing keys from DEFAULTS."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            return {**DEFAULTS, **saved}
        except Exception:
            pass
    return DEFAULTS.copy()


def save_config(config: dict) -> None:
    """Persist config to config.json (never includes the GitHub token)."""
    safe = {k: v for k, v in config.items() if k != "github_token"}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(safe, f, indent=2, ensure_ascii=False)


def get_github_token() -> str:
    return keyring.get_password(KEYRING_SERVICE, KEYRING_GITHUB) or ""


def set_github_token(token: str) -> None:
    keyring.set_password(KEYRING_SERVICE, KEYRING_GITHUB, token)
