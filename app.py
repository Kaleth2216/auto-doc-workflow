"""Auto Doc Workflow — CustomTkinter UI."""
from __future__ import annotations

import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Callable

import customtkinter as ctk

from config import DEFAULTS, get_github_token, load_config, save_config, set_github_token
from services import ServiceManager

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ── Reusable widget ───────────────────────────────────────────────────────────


class StatusDot(ctk.CTkFrame):
    """Colored circle indicator (●) with a text label."""

    _COLORS = {
        "red": "#FF4D4D",
        "yellow": "#FFBB00",
        "green": "#00CC66",
    }

    def __init__(self, parent: ctk.CTkFrame, label: str, **kw) -> None:
        super().__init__(parent, fg_color="transparent", **kw)
        self._dot = ctk.CTkLabel(
            self,
            text="●",
            text_color=self._COLORS["red"],
            font=ctk.CTkFont(size=20),
        )
        self._dot.pack(side="left", padx=(0, 5))
        ctk.CTkLabel(self, text=label, font=ctk.CTkFont(size=13)).pack(
            side="left"
        )

    def set(self, color: str) -> None:
        self._dot.configure(
            text_color=self._COLORS.get(color, self._COLORS["red"])
        )


# ── Configuration window ──────────────────────────────────────────────────────


class ConfigWindow(ctk.CTkToplevel):
    def __init__(
        self,
        parent: ctk.CTk,
        config: dict,
        on_save: Callable[[dict], None],
    ) -> None:
        super().__init__(parent)
        self.title("Configuración — Auto Doc Workflow")
        self.geometry("520x560")
        self.resizable(False, False)
        self.grab_set()
        self.focus()

        self._cfg = config.copy()
        self._on_save = on_save
        self._build()

    # ── Build ──────────────────────────────────────────────────────────────

    def _build(self) -> None:
        outer = ctk.CTkFrame(self)
        outer.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            outer,
            text="⚙  Configuración",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", padx=4, pady=(4, 14))

        # ── Field factory ────────────────────────────────────────────────
        def field(
            lbl: str, default: str = "", secret: bool = False
        ) -> ctk.CTkEntry:
            ctk.CTkLabel(
                outer, text=lbl, font=ctk.CTkFont(size=12)
            ).pack(anchor="w", padx=4, pady=(6, 1))
            e = ctk.CTkEntry(
                outer, width=460, show="●" if secret else ""
            )
            e.pack(padx=4, pady=(0, 0))
            if default:
                e.insert(0, default)
            return e

        self._token = field(
            "GitHub Token", get_github_token(), secret=True
        )
        self._repo = field(
            "URL del repositorio  (owner/repo)",
            self._cfg.get("repo_url", ""),
        )
        self._model = field(
            "Modelo de Ollama",
            self._cfg.get("ollama_model", DEFAULTS["ollama_model"]),
        )
        self._port = field(
            "Puerto de n8n",
            str(self._cfg.get("n8n_port", DEFAULTS["n8n_port"])),
        )
        self._n8n_key = field(
            "n8n API Key (opcional — necesaria si n8n tiene auth habilitado)",
            self._cfg.get("n8n_api_key", ""),
            secret=True,
        )
        self._webhook_id = field(
            "GitHub Webhook ID (opcional — si ya existe el webhook en el repo)",
            self._cfg.get("github_webhook_id", ""),
        )

        # ── Docker compose dir with browse ───────────────────────────────
        ctk.CTkLabel(
            outer,
            text="Directorio de Docker Compose",
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w", padx=4, pady=(6, 1))

        dir_row = ctk.CTkFrame(outer, fg_color="transparent")
        dir_row.pack(fill="x", padx=4, pady=(0, 0))

        self._dir = ctk.CTkEntry(dir_row, width=396)
        self._dir.pack(side="left")
        self._dir.insert(
            0, self._cfg.get("docker_compose_dir", DEFAULTS["docker_compose_dir"])
        )
        ctk.CTkButton(
            dir_row, text="…", width=55, command=self._browse
        ).pack(side="left", padx=(6, 0))

        # ── Buttons ───────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(outer, fg_color="transparent")
        btn_row.pack(fill="x", padx=4, pady=(18, 4))
        ctk.CTkButton(
            btn_row,
            text="Cancelar",
            width=110,
            fg_color="gray40",
            hover_color="gray30",
            command=self.destroy,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            btn_row, text="Guardar", width=110, command=self._save
        ).pack(side="right")

    # ── Callbacks ──────────────────────────────────────────────────────────

    def _browse(self) -> None:
        d = filedialog.askdirectory(parent=self)
        if d:
            self._dir.delete(0, "end")
            self._dir.insert(0, d)

    def _save(self) -> None:
        try:
            port = int(self._port.get().strip())
        except ValueError:
            messagebox.showerror(
                "Error", "El puerto de n8n debe ser un número.", parent=self
            )
            return

        token = self._token.get().strip()
        if token:
            set_github_token(token)

        self._cfg.update(
            {
                "repo_url": self._repo.get().strip(),
                "ollama_model": self._model.get().strip(),
                "n8n_port": port,
                "n8n_api_key": self._n8n_key.get().strip(),
                "github_webhook_id": self._webhook_id.get().strip(),
                "docker_compose_dir": self._dir.get().strip(),
            }
        )
        save_config(self._cfg)
        self._on_save(self._cfg)
        self.destroy()


# ── Main window ───────────────────────────────────────────────────────────────


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Auto Doc Workflow")
        self.geometry("740x640")
        self.minsize(620, 520)

        self._cfg = load_config()
        self._svc = ServiceManager(self._log)
        self._busy = False

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Open config automatically on first run
        if not self._cfg.get("repo_url"):
            self.after(400, self._open_config)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # ── Header ────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, corner_radius=0)
        hdr.pack(fill="x")

        ctk.CTkLabel(
            hdr,
            text="Auto Doc Workflow",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left", padx=16, pady=12)

        ctk.CTkButton(
            hdr,
            text="⚙  Configuración",
            width=150,
            command=self._open_config,
        ).pack(side="right", padx=14, pady=10)

        # ── Status card ───────────────────────────────────────────────────
        card = ctk.CTkFrame(self)
        card.pack(fill="x", padx=12, pady=(10, 0))

        ctk.CTkLabel(
            card,
            text="Estado de Servicios",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=14, pady=(10, 6))

        dots_row = ctk.CTkFrame(card, fg_color="transparent")
        dots_row.pack(fill="x", padx=10, pady=(0, 12))

        self._dots: dict[str, StatusDot] = {}
        for key, lbl in [
            ("docker", "Docker"),
            ("n8n", "n8n"),
            ("ngrok", "ngrok"),
            ("webhook", "Webhook"),
        ]:
            dot = StatusDot(dots_row, lbl)
            dot.pack(side="left", padx=20)
            self._dots[key] = dot

        # ── ngrok URL row ─────────────────────────────────────────────────
        url_row = ctk.CTkFrame(self)
        url_row.pack(fill="x", padx=12, pady=(8, 0))

        ctk.CTkLabel(
            url_row,
            text="URL ngrok:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left", padx=(14, 6), pady=10)

        self._url_var = tk.StringVar(value="—")
        ctk.CTkLabel(
            url_row,
            textvariable=self._url_var,
            text_color="#4FC3F7",
            font=ctk.CTkFont(family="Consolas", size=13),
        ).pack(side="left", pady=10)

        ctk.CTkButton(
            url_row,
            text="Copiar",
            width=80,
            command=self._copy_url,
        ).pack(side="right", padx=12, pady=8)

        # ── Action buttons ────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(10, 0))

        self._btn_start = ctk.CTkButton(
            btn_row,
            text="▶  Iniciar todo",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            height=42,
            width=190,
            command=self._start_all,
        )
        self._btn_start.pack(side="left", padx=(0, 10))

        self._btn_stop = ctk.CTkButton(
            btn_row,
            text="■  Detener todo",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#B71C1C",
            hover_color="#7F0000",
            height=42,
            width=190,
            command=self._stop_all,
        )
        self._btn_stop.pack(side="left")

        # ── Logs ──────────────────────────────────────────────────────────
        log_hdr = ctk.CTkFrame(self, fg_color="transparent")
        log_hdr.pack(fill="x", padx=14, pady=(12, 2))

        ctk.CTkLabel(
            log_hdr,
            text="Logs",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            log_hdr,
            text="Limpiar",
            width=72,
            height=26,
            fg_color="gray40",
            hover_color="gray30",
            font=ctk.CTkFont(size=11),
            command=self._clear_logs,
        ).pack(side="right")

        self._log_box = ctk.CTkTextbox(
            self,
            wrap="word",
            state="disabled",
            font=ctk.CTkFont(family="Consolas", size=11),
        )
        self._log_box.pack(fill="both", expand=True, padx=12, pady=(0, 10))

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _open_config(self) -> None:
        ConfigWindow(self, self._cfg, self._on_config_saved)

    def _on_config_saved(self, new_cfg: dict) -> None:
        self._cfg = new_cfg
        self._log("Configuración guardada.")

    def _log(self, msg: str) -> None:
        ts = datetime.datetime.now().strftime("%H:%M:%S")

        def _do() -> None:
            # El textbox debe habilitarse temporalmente para insertar texto
            self._log_box.configure(state="normal")
            self._log_box.insert("end", f"[{ts}] {msg}\n")
            # Desplaza automáticamente al final para mostrar el último mensaje
            self._log_box.see("end")
            self._log_box.configure(state="disabled")

        # self.after(0) envía la actualización al hilo principal de Tkinter
        # (necesario porque los logs se generan desde hilos secundarios)
        self.after(0, _do)

    def _clear_logs(self) -> None:
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")

    def _set_status(self, service: str, color: str) -> None:
        def _do() -> None:
            if service in self._dots:
                self._dots[service].set(color)
            # Update ngrok URL label when status changes
            if service == "ngrok":
                self._url_var.set(
                    self._svc.ngrok_url if color == "green" else "—"
                )

        self.after(0, _do)

    def _copy_url(self) -> None:
        url = self._url_var.get()
        if url and url != "—":
            self.clipboard_clear()
            self.clipboard_append(url)
            self._log("URL copiada al portapapeles.")
        else:
            self._log("[!] No hay URL de ngrok disponible.")

    def _set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self._btn_start.configure(state=state)
        self._btn_stop.configure(state=state)
        self._busy = busy

    def _start_all(self) -> None:
        if self._busy:
            return
        self._set_busy(True)
        # Se agrega el token de GitHub al config en memoria (nunca se guarda en disco)
        cfg = {**self._cfg, "github_token": get_github_token()}
        self._svc.start_all(cfg, self._set_status, self._on_start_done)

    def _on_start_done(self, success: bool) -> None:
        self.after(0, lambda: self._set_busy(False))

    def _stop_all(self) -> None:
        if self._busy:
            return
        self._set_busy(True)
        self._svc.stop_all(self._cfg, self._set_status, self._on_stop_done)

    def _on_stop_done(self) -> None:
        self.after(0, lambda: self._set_busy(False))

    def _on_close(self) -> None:
        # Terminate ngrok quietly when closing the window
        self._svc.terminate_ngrok()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
