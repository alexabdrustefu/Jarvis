"""Local reminders, routines and system diagnostics."""

import os
import threading
from datetime import datetime
from queue import Empty, Queue

import customtkinter as ctk
from tkinter import messagebox

from core.local_features import parse_reminder
from gui.services.diagnostics import collect_diagnostics


class LocalToolsView(ctk.CTkFrame):
    def __init__(self, master, store, on_command=None, microphone=None, router=None):
        super().__init__(master, fg_color="transparent")
        self.store, self.on_command, self.microphone = store, on_command, microphone
        self.router = router
        self.bridge = None
        self._diagnostics_queue = Queue()
        self._diagnostics_running = False
        self._diagnostics_pending = False
        self._diagnostics_poll_id = None
        self._closed = False
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.body.grid(row=0, column=0, sticky="nsew")
        self.body.grid_columnconfigure((0, 1), weight=1)
        self.body.grid_rowconfigure(2, weight=2)
        self.body.grid_rowconfigure(3, weight=1)
        ctk.CTkLabel(self.body, text="J.A.R.V.I.S.  /  CONTROL DESK", font=("Consolas", 10, "bold"),
                     text_color="#67E8F9").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        ctk.CTkLabel(self.body, text="Agenda e automazioni", font=("Segoe UI", 23, "bold"),
                     text_color="#E6F1FF").grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 14))
        self._build_reminders()
        self._build_routines()
        self._build_preferences()
        self._build_diagnostics()
        self.refresh()

    def _panel(self, title, row, col, span=1):
        frame = ctk.CTkFrame(self.body, fg_color="#101A2B", corner_radius=16,
                             border_width=1, border_color="#20344C")
        frame.grid(row=row, column=col, columnspan=span, sticky="nsew", padx=5, pady=5)
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(frame, text=title, font=("Segoe UI", 15, "bold"), text_color="#F0F6FF").grid(
            row=0, column=0, sticky="w", padx=16, pady=(14, 9))
        return frame

    def _build_reminders(self):
        panel = self._panel("Promemoria e attività", 3, 0)
        self.reminder_entry = ctk.CTkEntry(panel, placeholder_text="Es. ricordami di chiamare Luca domani alle 9")
        self.reminder_entry.grid(row=1, column=0, sticky="ew", padx=12, pady=4)
        ctk.CTkButton(panel, text="Aggiungi", command=self.add_reminder).grid(row=1, column=1, padx=(0, 12))
        self.reminder_list = ctk.CTkScrollableFrame(panel, height=210, fg_color="transparent")
        self.reminder_list.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=8, pady=5)
        self.reminder_list.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(panel, text="Comandi chat: ‘mostra promemoria’, ‘completa 2’.",
                     font=("Segoe UI", 10), text_color="#91A4BE").grid(row=3, column=0, columnspan=2, sticky="w", padx=14, pady=(0, 10))

    def add_reminder(self):
        text = self.reminder_entry.get().strip()
        if not text:
            return
        title, due = parse_reminder(text)
        if title.lower().startswith(("ricordami di ", "aggiungi attività ", "aggiungi attivita ")):
            for prefix in ("ricordami di ", "aggiungi attività ", "aggiungi attivita "):
                if title.lower().startswith(prefix):
                    title = title[len(prefix):]
        try:
            self.store.add_reminder(title, due)
            self.reminder_entry.delete(0, "end")
            self.refresh()
        except ValueError as error:
            messagebox.showerror("Promemoria", str(error), parent=self)

    def _build_routines(self):
        panel = self._panel("Routine personalizzabili", 2, 0, span=2)
        panel.grid_columnconfigure(1, weight=1)
        self.routine_name = ctk.CTkEntry(panel, placeholder_text="Nome, es. modalità lavoro")
        self.routine_name.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=4)
        ctk.CTkLabel(panel, text="EDITOR DEI PASSAGGI", font=("Consolas", 9, "bold"),
                     text_color="#67E8F9").grid(row=2, column=0, sticky="w", padx=14, pady=(8, 2))
        ctk.CTkLabel(panel, text="ROUTINE SALVATE", font=("Consolas", 9, "bold"),
                     text_color="#67E8F9").grid(row=2, column=1, sticky="w", padx=10, pady=(8, 2))
        self.routine_actions = {
            "Meteo": "weather", "Notizie": "news", "Ora": "time",
            "Abbassa volume": "volume_down", "Apri Google": "open_browser",
        }
        self.routine_sequence = []
        self.action_menu = ctk.CTkOptionMenu(panel, values=list(self.routine_actions))
        self.action_menu.grid(row=3, column=0, sticky="ew", padx=12, pady=5)
        ctk.CTkButton(panel, text="＋ Aggiungi", command=self.add_routine_step).grid(
            row=3, column=1, sticky="w", padx=8, pady=5)
        self.steps_list = ctk.CTkScrollableFrame(panel, height=108, fg_color="#0B1422", corner_radius=10)
        self.steps_list.grid(row=4, column=0, sticky="nsew", padx=(12, 5), pady=4)
        self.steps_list.grid_columnconfigure(0, weight=1)
        self.routine_list = ctk.CTkScrollableFrame(panel, height=108, fg_color="#0B1422", corner_radius=10)
        self.routine_list.grid(row=4, column=1, sticky="nsew", padx=(5, 12), pady=4)
        self.routine_list.grid_columnconfigure(0, weight=1)
        self.selected_step = None
        step_controls = ctk.CTkFrame(panel, fg_color="transparent")
        step_controls.grid(row=5, column=0, sticky="w", padx=8)
        for label, delta in (("↑", -1), ("↓", 1)):
            ctk.CTkButton(step_controls, text=label, width=36,
                          command=lambda amount=delta: self.move_routine_step(amount)).pack(side="left", padx=3)
        ctk.CTkButton(step_controls, text="Rimuovi passaggio", width=132,
                      command=self.remove_routine_step).pack(side="left", padx=3)
        ctk.CTkButton(panel, text="Salva routine", command=self.save_routine,
                      fg_color="#9A482C", hover_color="#C65C35").grid(row=5, column=1, padx=12, pady=8, sticky="e")

    def save_routine(self):
        name = self.routine_name.get().strip()
        steps = list(self.routine_sequence)
        try:
            self.store.save_routine(name, steps)
            self.routine_name.delete(0, "end")
            self.routine_sequence.clear()
            self.selected_step = None
            self._refresh_step_list()
            self.refresh()
        except ValueError as error:
            messagebox.showerror("Routine", str(error), parent=self)

    def add_routine_step(self):
        self.routine_sequence.append(self.routine_actions[self.action_menu.get()])
        self.selected_step = len(self.routine_sequence) - 1
        self._refresh_step_list()

    def move_routine_step(self, delta):
        if self.selected_step is None:
            return
        index = self.selected_step
        target = index + delta
        if 0 <= target < len(self.routine_sequence):
            self.routine_sequence[index], self.routine_sequence[target] = self.routine_sequence[target], self.routine_sequence[index]
            self.selected_step = target
            self._refresh_step_list()

    def remove_routine_step(self):
        if self.selected_step is not None:
            self.routine_sequence.pop(self.selected_step)
            self.selected_step = None
            self._refresh_step_list()

    def _refresh_step_list(self):
        labels = {value: label for label, value in self.routine_actions.items()}
        for child in self.steps_list.winfo_children():
            child.destroy()
        for index, action in enumerate(self.routine_sequence, start=1):
            row_index = index - 1
            ctk.CTkButton(
                self.steps_list, text=f"{index:02d}   {labels[action]}", height=28,
                corner_radius=7, anchor="w",
                fg_color="#173650" if row_index == self.selected_step else "transparent",
                hover_color="#173650", text_color="#DCEBFA",
                command=lambda row=row_index: self._select_routine_step(row),
            ).grid(row=row_index, column=0, sticky="ew", padx=3, pady=2)

    def _select_routine_step(self, index):
        self.selected_step = index
        self._refresh_step_list()

    def _build_preferences(self):
        panel = self._panel("PREFERENZE  /  VOCE E CONTESTO", 3, 1)
        prefs = self.store.get_preferences()
        self.voice_var = ctk.BooleanVar(value=bool(prefs["voice_replies"]))
        ctk.CTkCheckBox(panel, text="Leggi le risposte in chat", variable=self.voice_var,
                        command=lambda: self.store.set_preference("voice_replies", self.voice_var.get())).grid(
                            row=1, column=0, sticky="w", padx=14, pady=7)
        ctk.CTkLabel(panel, text="Località predefinita meteo", text_color="#91A4BE").grid(row=2, column=0, sticky="w", padx=14)
        self.location = ctk.CTkEntry(panel, placeholder_text="Es. Milano")
        self.location.insert(0, prefs.get("location", ""))
        self.location.grid(row=3, column=0, sticky="ew", padx=12, pady=6)
        ctk.CTkButton(panel, text="Salva", width=78, command=self.save_location).grid(row=3, column=1, padx=10)
        ctk.CTkLabel(panel, text="Memorizzate solo su questo PC. Nessun account aggiuntivo.",
                     font=("Segoe UI", 10), text_color="#91A4BE").grid(row=4, column=0, columnspan=2, sticky="w", padx=14, pady=(3, 10))
        ctk.CTkLabel(panel, text="Voce Edge TTS", text_color="#91A4BE").grid(row=5, column=0, sticky="w", padx=14)
        self.voice_menu = ctk.CTkOptionMenu(panel, values=["it-IT-IsabellaNeural", "it-IT-DiegoNeural"],
                                            command=lambda value: self.store.set_preference("voice", value))
        self.voice_menu.set(prefs.get("voice", "it-IT-IsabellaNeural"))
        self.voice_menu.grid(row=6, column=0, sticky="w", padx=12, pady=(4, 12))
        self.rate_menu = ctk.CTkOptionMenu(panel, values=["Lenta", "Normale", "Veloce"], command=self.save_rate)
        self.rate_menu.set({"-15%": "Lenta", "+0%": "Normale", "+15%": "Veloce"}.get(prefs.get("speech_rate"), "Normale"))
        self.rate_menu.grid(row=6, column=1, sticky="e", padx=12, pady=(4, 12))
        ctk.CTkLabel(panel, text="Modello AI", text_color="#91A4BE").grid(row=7, column=0, sticky="w", padx=14)
        self.provider_menu = ctk.CTkOptionMenu(
            panel, values=["Automatico", "Ollama", "LM Studio", "Groq facoltativo"], command=self.set_provider
        )
        provider_names = {"auto": "Automatico", "ollama": "Ollama", "lmstudio": "LM Studio", "groq": "Groq facoltativo"}
        self.provider_menu.set(provider_names.get(prefs.get("llm_provider", "auto"), "Automatico"))
        self.provider_menu.grid(row=8, column=0, sticky="w", padx=12, pady=(4, 10))
        ctk.CTkLabel(panel, text="Il modello locale non richiede account né API key.",
                     font=("Segoe UI", 10), text_color="#91A4BE").grid(row=8, column=1, sticky="e", padx=8)

    def save_location(self):
        self.store.set_preference("location", self.location.get().strip())

    def save_rate(self, value):
        self.store.set_preference("speech_rate", {"Lenta": "-15%", "Normale": "+0%", "Veloce": "+15%"}[value])

    def set_provider(self, value):
        preference = {"Automatico": "auto", "Ollama": "ollama", "LM Studio": "lmstudio", "Groq facoltativo": "groq"}[value]
        self.store.set_preference("llm_provider", preference)
        if self.router and hasattr(self.router.ai, "provider_preference"):
            self.router.ai.provider_preference = preference
        self.run_diagnostics()

    def _build_diagnostics(self):
        panel = self._panel("DIAGNOSTICA  /  STATO DEL SISTEMA", 4, 0, span=2)
        self.diagnostics = ctk.CTkLabel(panel, text="", justify="left", anchor="w", text_color="#C9D5E5")
        self.diagnostics.grid(row=1, column=0, sticky="ew", padx=14, pady=5)
        ctk.CTkButton(panel, text="Aggiorna controlli", command=self.run_diagnostics).grid(row=2, column=0, sticky="w", padx=12, pady=8)
        ctk.CTkLabel(panel, text="HTTP + WebSocket /ws · 8765    Socket JSON · 8766",
                     font=("Consolas", 9), text_color="#91A4BE").grid(row=3, column=0, sticky="w", padx=14, pady=(5, 2))
        self.bridge_button = ctk.CTkButton(panel, text="Avvia bridge per web", command=self.toggle_bridge)
        self.bridge_button.grid(row=4, column=0, sticky="w", padx=12, pady=(4, 12))
        self.run_diagnostics()

    def toggle_bridge(self):
        if self.bridge is not None:
            self.bridge.stop()
            self.bridge = None
            self.bridge_button.configure(text="Avvia bridge per web")
            return
        if not self.router:
            return
        try:
            from api.bootstrap import create_local_bridge
            self.bridge = create_local_bridge(self.router)
            self.bridge.start()
            self.bridge_button.configure(text="Arresta bridge locale")
        except OSError as error:
            messagebox.showerror("Bridge locale", f"Non riesco ad aprire le porte locali: {error}", parent=self)

    def on_close(self):
        self._closed = True
        if self._diagnostics_poll_id is not None:
            try:
                self.after_cancel(self._diagnostics_poll_id)
            except Exception:
                pass
            self._diagnostics_poll_id = None
        if self.bridge is not None:
            self.bridge.stop()
            self.bridge = None

    def run_diagnostics(self):
        if self._closed:
            return
        if self._diagnostics_running:
            self._diagnostics_pending = True
            return
        self._diagnostics_running = True
        self.diagnostics.configure(text="Controllo database, provider e dispositivi…")

        def collect():
            try:
                result = collect_diagnostics(
                    self.store, self.router, self.microphone,
                    groq_configured=bool(os.getenv("GROQ_API_KEY")),
                )
            except Exception as error:
                result = [f"Diagnostica non disponibile: {error}"]
            self._diagnostics_queue.put(result)

        threading.Thread(target=collect, name="jarvis-diagnostics", daemon=True).start()
        self._poll_diagnostics()

    def _poll_diagnostics(self):
        self._diagnostics_poll_id = None
        if self._closed or not self.winfo_exists():
            return
        try:
            result = self._diagnostics_queue.get_nowait()
        except Empty:
            self._diagnostics_poll_id = self.after(100, self._poll_diagnostics)
            return
        self._diagnostics_running = False
        self.diagnostics.configure(text="\n".join(result))
        if self._diagnostics_pending:
            self._diagnostics_pending = False
            self.run_diagnostics()

    def refresh(self):
        for child in self.reminder_list.winfo_children():
            child.destroy()
        for row, (ident, title, due, status) in enumerate(self.store.list_reminders()):
            due_label = datetime.fromisoformat(due).strftime("%d/%m %H:%M") if due else "senza scadenza"
            ctk.CTkLabel(self.reminder_list, text=f"#{ident}  {title}\n      {due_label}", anchor="w",
                         justify="left", text_color="#C9D5E5").grid(row=row, column=0, sticky="ew", pady=3)
            ctk.CTkButton(self.reminder_list, text="✓", width=34, command=lambda i=ident: self._complete(i)).grid(row=row, column=1, padx=3)
            ctk.CTkButton(self.reminder_list, text="×", width=34, fg_color="#48252A", command=lambda i=ident: self._delete(i)).grid(row=row, column=2, padx=3)
        for child in self.routine_list.winfo_children():
            child.destroy()
        for row, (name, steps) in enumerate(self.store.list_routines()):
            ctk.CTkLabel(self.routine_list, text=f"{name} · {len(steps)} azioni", anchor="w").grid(row=row, column=0, sticky="ew", padx=6)
            ctk.CTkButton(self.routine_list, text="Avvia in chat", width=102,
                          command=lambda n=name: self.on_command(f"avvia {n}") if self.on_command else None).grid(row=row, column=1, padx=4, pady=3)
            ctk.CTkButton(self.routine_list, text="×", width=34, fg_color="#48252A",
                          command=lambda n=name: self._delete_routine(n)).grid(row=row, column=2, padx=4)

    def _delete_routine(self, name):
        if messagebox.askyesno("Elimina routine", f"Vuoi eliminare la routine ‘{name}’?", parent=self):
            self.store.delete_routine(name)
            self.refresh()

    def _complete(self, ident):
        self.store.complete_reminder(ident)
        self.refresh()

    def _delete(self, ident):
        self.store.delete_reminder(ident)
        self.refresh()
