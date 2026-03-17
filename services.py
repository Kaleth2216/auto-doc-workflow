"""Background service manager: Docker, ngrok, n8n and GitHub webhook."""
from __future__ import annotations

import subprocess
import threading
import time
from typing import Callable, Optional

import requests


class ServiceManager:
    """Handles start/stop lifecycle for all services in background threads."""

    def __init__(self, log_fn: Callable[[str], None]) -> None:
        self._log = log_fn
        self._ngrok_proc: Optional[subprocess.Popen] = None
        self.ngrok_url: Optional[str] = None
        self._lock = threading.Lock()

    # ── Public API ────────────────────────────────────────────────────────────

    def start_all(
        self,
        config: dict,
        status_fn: Callable[[str, str], None],
        done_fn: Callable[[bool], None],
    ) -> None:
        threading.Thread(
            target=self._run_start,
            args=(config, status_fn, done_fn),
            daemon=True,
        ).start()

    def stop_all(
        self,
        config: dict,
        status_fn: Callable[[str, str], None],
        done_fn: Callable[[], None],
    ) -> None:
        threading.Thread(
            target=self._run_stop,
            args=(config, status_fn, done_fn),
            daemon=True,
        ).start()

    def terminate_ngrok(self) -> None:
        """Silently kill the ngrok process (called on app close)."""
        with self._lock:
            if self._ngrok_proc and self._ngrok_proc.poll() is None:
                self._ngrok_proc.terminate()
                self._ngrok_proc = None
        self.ngrok_url = None

    # ── Start flow ────────────────────────────────────────────────────────────

    def _run_start(
        self,
        config: dict,
        status_fn: Callable,
        done_fn: Callable,
    ) -> None:
        success = False
        try:
            port = int(config.get("n8n_port", 5678))
            docker_dir = config.get("docker_compose_dir", ".")
            github_token = config.get("github_token", "")
            repo = config.get("repo_url", "")
            n8n_key = config.get("n8n_api_key", "")
            webhook_id = config.get("github_webhook_id", "")

            # ── Step 1: Docker compose up ─────────────────────────────────
            status_fn("docker", "yellow")
            self._log("▶ Levantando Docker (docker compose up -d)…")
            result = subprocess.run(
                ["docker", "compose", "up", "-d"],
                cwd=docker_dir,
                capture_output=True,
                text=True,
                timeout=180,
            )
            if result.returncode != 0:
                self._log(f"[✗] docker compose up falló:\n{result.stderr.strip()}")
                status_fn("docker", "red")
                return
            if result.stdout.strip():
                self._log(result.stdout.strip())
            self._log("[✓] Docker iniciado")
            status_fn("docker", "green")

            # ── Step 2: Wait for n8n ──────────────────────────────────────
            status_fn("n8n", "yellow")
            self._log(f"⏳ Esperando n8n en localhost:{port}…")
            if not self._wait_for_n8n(port, timeout=120):
                self._log("[✗] n8n no respondió en 120 s")
                status_fn("n8n", "red")
                return
            self._log("[✓] n8n disponible")
            status_fn("n8n", "green")

            # ── Step 3: Start ngrok ───────────────────────────────────────
            status_fn("ngrok", "yellow")
            self._log(f"▶ Iniciando ngrok → puerto {port}…")
            with self._lock:
                if self._ngrok_proc and self._ngrok_proc.poll() is None:
                    self._ngrok_proc.terminate()
                self._ngrok_proc = subprocess.Popen(
                    ["ngrok", "http", str(port)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            time.sleep(3)
            url = self._fetch_ngrok_url()
            if not url:
                self._log("[✗] No se pudo obtener la URL pública de ngrok")
                status_fn("ngrok", "red")
                return
            self.ngrok_url = url
            self._log(f"[✓] ngrok URL: {url}")
            status_fn("ngrok", "green")

            # ── Step 4: Update GitHub webhook ─────────────────────────────
            status_fn("webhook", "yellow")
            webhook_url = f"{url}/webhook/github-push"
            self._log(f"▶ Actualizando webhook de GitHub…\n   → {webhook_url}")
            ok = self._update_github_webhook(github_token, repo, webhook_url, webhook_id)
            if ok:
                self._log("[✓] Webhook de GitHub actualizado")
                status_fn("webhook", "green")
            else:
                status_fn("webhook", "red")
                # non-fatal: continue so n8n workflow still gets activated

            # ── Step 5: Activate n8n workflows ────────────────────────────
            self._log("▶ Activando workflows en n8n…")
            n = self._toggle_n8n_workflows(port, n8n_key, activate=True)
            self._log(f"[✓] {n} workflow(s) activado(s)")

            success = True
            self._log("══════ Todo iniciado correctamente ══════")

        except FileNotFoundError as e:
            self._log(
                f"[✗] Comando no encontrado: '{e.filename}'. "
                "¿Está instalado y en el PATH?"
            )
        except subprocess.TimeoutExpired:
            self._log("[✗] Tiempo de espera agotado")
        except Exception as e:
            self._log(f"[✗] Error inesperado: {e}")
        finally:
            done_fn(success)

    # ── Stop flow ─────────────────────────────────────────────────────────────

    def _run_stop(
        self,
        config: dict,
        status_fn: Callable,
        done_fn: Callable,
    ) -> None:
        try:
            port = int(config.get("n8n_port", 5678))
            docker_dir = config.get("docker_compose_dir", ".")
            n8n_key = config.get("n8n_api_key", "")

            # ── Step 1: Deactivate n8n workflows ──────────────────────────
            self._log("▶ Desactivando workflows en n8n…")
            try:
                n = self._toggle_n8n_workflows(port, n8n_key, activate=False)
                self._log(f"[✓] {n} workflow(s) desactivado(s)")
            except Exception as e:
                self._log(f"[!] No se pudieron desactivar workflows: {e}")

            # ── Step 2: Stop ngrok ────────────────────────────────────────
            self._log("▶ Deteniendo ngrok…")
            self.terminate_ngrok()
            status_fn("ngrok", "red")
            status_fn("webhook", "red")
            self._log("[✓] ngrok detenido")

            # ── Step 3: Docker compose down ───────────────────────────────
            status_fn("docker", "yellow")
            status_fn("n8n", "yellow")
            self._log("▶ Ejecutando docker compose down…")
            result = subprocess.run(
                ["docker", "compose", "down"],
                cwd=docker_dir,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                self._log(f"[✗] docker compose down:\n{result.stderr.strip()}")
            else:
                if result.stdout.strip():
                    self._log(result.stdout.strip())
                self._log("[✓] Docker detenido")
            status_fn("docker", "red")
            status_fn("n8n", "red")
            self._log("══════ Todo detenido ══════")

        except Exception as e:
            self._log(f"[✗] Error al detener: {e}")
        finally:
            done_fn()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _wait_for_n8n(self, port: int, timeout: int = 120) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                r = requests.get(
                    f"http://localhost:{port}/healthz", timeout=3
                )
                if r.status_code < 500:
                    return True
            except Exception:
                pass
            time.sleep(2)
        return False

    def _fetch_ngrok_url(self, retries: int = 12) -> Optional[str]:
        for _ in range(retries):
            try:
                r = requests.get(
                    "http://localhost:4040/api/tunnels", timeout=3
                )
                tunnels = r.json().get("tunnels", [])
                for t in tunnels:
                    if t.get("proto") == "https":
                        return t["public_url"]
                if tunnels:
                    return tunnels[0]["public_url"]
            except Exception:
                pass
            time.sleep(1)
        return None

    def _update_github_webhook(
        self, token: str, repo: str, webhook_url: str, webhook_id: str = ""
    ) -> bool:
        if not token or not repo:
            self._log(
                "[!] GitHub token o repo no configurados — webhook omitido"
            )
            return False
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        api = f"https://api.github.com/repos/{repo}/hooks"
        payload: dict = {
            "active": True,
            "config": {"url": webhook_url, "content_type": "json"},
        }
        try:
            if webhook_id:
                # Use the known webhook ID directly — no listing needed
                self._log(f"   Usando webhook ID: {webhook_id}")
                r = requests.patch(
                    f"{api}/{webhook_id}", json=payload, headers=headers, timeout=10
                )
            else:
                hooks_r = requests.get(api, headers=headers, timeout=10)
                hooks_r.raise_for_status()
                hooks = hooks_r.json()
                if hooks:
                    hook_id = hooks[0]["id"]
                    r = requests.patch(
                        f"{api}/{hook_id}", json=payload, headers=headers, timeout=10
                    )
                else:
                    payload["name"] = "web"
                    payload["events"] = ["push"]
                    r = requests.post(api, json=payload, headers=headers, timeout=10)
            r.raise_for_status()
            return True
        except requests.HTTPError as e:
            body = (e.response.text[:300] if e.response else "") or ""
            self._log(
                f"[✗] GitHub API {e.response.status_code}: {body}"
            )
            return False
        except Exception as e:
            self._log(f"[✗] GitHub API error: {e}")
            return False

    def _toggle_n8n_workflows(
        self, port: int, api_key: str, *, activate: bool
    ) -> int:
        base = f"http://localhost:{port}/api/v1"
        headers = {"X-N8N-API-KEY": api_key} if api_key else {}
        action = "activate" if activate else "deactivate"
        count = 0
        try:
            r = requests.get(f"{base}/workflows", headers=headers, timeout=5)
            r.raise_for_status()
            workflows = r.json().get("data", [])
            for wf in workflows:
                wf_id = wf["id"]
                r2 = requests.post(
                    f"{base}/workflows/{wf_id}/{action}",
                    headers=headers,
                    timeout=5,
                )
                if r2.status_code < 400:
                    count += 1
        except Exception as e:
            self._log(f"[!] n8n API: {e}")
        return count
