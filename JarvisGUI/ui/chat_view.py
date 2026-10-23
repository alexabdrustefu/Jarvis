"""Animated, persistent chat view; all Tk operations stay on the UI thread."""

import re
import threading
from collections import Counter
from datetime import datetime
from queue import Empty, Queue
from tkinter import BooleanVar, messagebox

import customtkinter as ctk


class TypingIndicator(ctk.CTkFrame):
    def __init__(self, master, label="JARVIS sta elaborando"):
        super().__init__(master, fg_color="#132238", corner_radius=12)
        self._phase = 0
        ctk.CTkLabel(
            self, text=label, font=("Segoe UI", 11), text_color="#91A4BE",
        ).pack(side="left", padx=(12, 5), pady=8)
        self.dots_canvas = ctk.CTkCanvas(
            self, width=47, height=24, bg="#132238", highlightthickness=0,
        )
        self.dots_canvas.pack(side="left", padx=(0, 8))
        self.dots = [
            self.dots_canvas.create_oval(4 + index * 13, 9, 10 + index * 13, 15,
                                         fill="#294158", outline="")
            for index in range(3)
        ]
        self._animate()

    def _animate(self):
        if not self.winfo_exists():
            return
        for index, dot in enumerate(self.dots):
            distance = (index - self._phase) % len(self.dots)
            color = ("#F2B84B", "#8BDFFF", "#294158")[min(distance, 2)]
            self.dots_canvas.itemconfigure(dot, fill=color)
        self._phase = (self._phase + 1) % len(self.dots)
        self.after(100, self._animate)


class ChatView(ctk.CTkFrame):
    PANEL = "#101A2B"
    TEXT = "#E6F1FF"
    MUTED = "#91A4BE"
    CYAN = "#67E8F9"
    GOLD = "#EAB45A"

    def __init__(self, master, handle_message, listen=None, speak=None,
                 clear_history=None, load_history=None, load_after=None):
        super().__init__(master, fg_color="transparent")
        self.handle_message = handle_message
        self.listen = listen
        self.speak = speak
        self.clear_history_callback = clear_history
        self.load_history_callback = load_history
        self.load_after_callback = load_after
        self._results = Queue()
        self._busy = False
        self._message_row = 0
        self._last_message_id = 0
        self._pending_echoes = Counter()
        self._indicator = None
        self._scroll_job = None
        self._speak_enabled = BooleanVar(master=self, value=False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(2, 7))
        toolbar.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            toolbar, text="LINK DIRETTO  /  CONVERSAZIONE SICURA",
            font=("Consolas", 9, "bold"), text_color=self.CYAN,
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            toolbar, text="Chat con J.A.R.V.I.S.", font=("Segoe UI", 24, "bold"),
            text_color=self.TEXT,
        ).grid(row=1, column=0, sticky="w")
        controls = ctk.CTkFrame(toolbar, fg_color="transparent")
        controls.grid(row=0, column=1, rowspan=2, sticky="e")
        self.speak_switch = ctk.CTkSwitch(
            controls, text="LEGGI RISPOSTE", variable=self._speak_enabled,
            font=("Consolas", 9), text_color=self.MUTED,
            progress_color="#0E7490", state="normal" if self.speak else "disabled",
        )
        self.speak_switch.pack(side="left", padx=(0, 12))
        ctk.CTkButton(
            controls, text="PULISCI", width=76, height=30,
            fg_color="#17263B", hover_color="#263B56", text_color=self.MUTED,
            font=("Consolas", 9, "bold"), command=self.clear_history,
        ).pack(side="left")

        prompts = ctk.CTkFrame(self, fg_color="transparent")
        prompts.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        for title, command in (
            ("METEO OGGI", "meteo oggi"),
            ("NOTIZIE", "dimmi le notizie"),
            ("EMAIL", "leggi le email"),
            ("AIUTO", "aiuto"),
        ):
            ctk.CTkButton(
                prompts, text=title, width=96, height=27, corner_radius=8,
                fg_color="#102338", hover_color="#173650", text_color="#8DBDD5",
                font=("Consolas", 9, "bold"),
                command=lambda value=command: self.send_message(value),
            ).pack(side="left", padx=(0, 7))

        panel = ctk.CTkFrame(self, fg_color=self.PANEL, corner_radius=16)
        panel.grid(row=2, column=0, sticky="nsew", padx=2, pady=2)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(0, weight=1)

        self.messages = ctk.CTkScrollableFrame(
            panel, fg_color="transparent", corner_radius=0,
        )
        self.messages.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=9, pady=(10, 5))
        self.messages.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkTextbox(
            panel, height=68, font=("Segoe UI", 13), wrap="word",
            corner_radius=10, border_width=1, border_color="#263B56",
            fg_color="#0B1422",
        )
        self.entry.grid(row=1, column=0, sticky="ew", padx=(13, 9), pady=(5, 13))
        self.entry.insert("1.0", "")
        self.entry.bind("<Control-Return>", self._on_send_shortcut)
        self.voice_button = ctk.CTkButton(
            panel, text="PARLA", width=94, height=42, corner_radius=10,
            fg_color="#123149", hover_color="#174766", text_color=self.CYAN,
            font=("Consolas", 10, "bold"), command=self.listen_once,
            state="normal" if self.listen else "disabled",
        )
        self.voice_button.grid(row=1, column=1, padx=(0, 8), pady=(5, 13))
        self.send_button = ctk.CTkButton(
            panel, text="INVIA  →", width=100, height=42, corner_radius=10,
            fg_color="#0369A1", hover_color="#0284C7", text_color="white",
            font=("Consolas", 10, "bold"), command=self.send,
        )
        self.send_button.grid(row=1, column=2, padx=(0, 13), pady=(5, 13))

        self._restore_history()
        self.bind("<Map>", self._on_chat_mapped, add="+")
        self.after(900, self._sync_external_history)
        self.entry.focus()

    def _restore_history(self):
        history = self.load_history_callback() if self.load_history_callback else []
        if history:
            for message in history:
                self._append_message(
                    message["role"], message["content"], message.get("created_at")
                )
                self._last_message_id = max(self._last_message_id, message.get("id", 0))
        else:
            self._append_message(
                "assistant", "Buongiorno, Boss. Sistemi pronti. Come posso assisterti?"
            )
        self._scroll_to_bottom()

    def _append_message(self, role: str, content: str, timestamp: str | None = None) -> None:
        is_user = role == "user"
        row = ctk.CTkFrame(self.messages, fg_color="transparent")
        row.grid(row=self._message_row, column=0, sticky="ew", padx=5, pady=5)
        row.grid_columnconfigure(0, weight=1)

        bubble = ctk.CTkFrame(
            row,
            fg_color="#123149" if is_user else "#172336",
            corner_radius=13,
            border_width=1,
            border_color="#1D5672" if is_user else "#66502B",
        )
        bubble.grid(row=0, column=1 if is_user else 0, sticky="e" if is_user else "w")
        bubble.grid_columnconfigure(0, weight=1)

        title = "TU" if is_user else "J.A.R.V.I.S."
        ctk.CTkLabel(
            bubble, text=title, font=("Consolas", 9, "bold"),
            text_color=self.CYAN if is_user else self.GOLD,
        ).grid(row=0, column=0, sticky="w", padx=(13, 8), pady=(9, 1))
        ctk.CTkLabel(
            bubble, text=self._format_timestamp(timestamp),
            font=("Consolas", 8), text_color="#74869D",
        ).grid(row=0, column=1, sticky="e", padx=(0, 12), pady=(9, 1))

        display_text = self._format_message(content)
        ctk.CTkLabel(
            bubble, text=display_text, font=("Segoe UI", 13),
            text_color=self.TEXT, justify="left", anchor="w",
            wraplength=620,
        ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=13, pady=(2, 10))
        if not is_user:
            ctk.CTkButton(
                bubble, text="COPIA", width=48, height=20, corner_radius=5,
                fg_color="transparent", hover_color="#263B56", text_color="#74869D",
                font=("Consolas", 8),
                command=lambda value=content: self._copy_message(value),
            ).grid(row=2, column=1, sticky="e", padx=8, pady=(0, 5))

        self._message_row += 1
        self._scroll_to_bottom()

    @staticmethod
    def _format_timestamp(timestamp: str | None) -> str:
        if not timestamp:
            return datetime.now().strftime("%H:%M")
        try:
            value = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return value.astimezone().strftime("%d/%m %H:%M")
        except ValueError:
            return datetime.now().strftime("%H:%M")

    @staticmethod
    def _format_message(content: str) -> str:
        content = re.sub(r"\*\*(.*?)\*\*", r"\1", content)
        content = re.sub(r"\*(.*?)\*", r"\1", content)
        return re.sub(r"`([^`]*)`", r"\1", content)

    def _copy_message(self, content: str):
        self.clipboard_clear()
        self.clipboard_append(content)

    def _scroll_to_bottom(self):
        # CTkScrollableFrame finishes sizing its canvas after the chat is mapped.
        # Defer and coalesce scroll requests so restored history is laid out first.
        if self._scroll_job is not None:
            try:
                self.after_cancel(self._scroll_job)
            except Exception:
                pass
        self._scroll_job = self.after(70, self._move_scroll_to_bottom)

    def _on_chat_mapped(self, _event=None):
        self._scroll_to_bottom()

    def _move_scroll_to_bottom(self):
        self._scroll_job = None
        if not self.winfo_exists() or not self.messages.winfo_exists():
            return
        canvas = self.messages._parent_canvas
        canvas.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.yview_moveto(1.0)

    def _show_indicator(self, label: str):
        self._indicator = TypingIndicator(self.messages, label)
        self._indicator.grid(row=self._message_row, column=0, sticky="w", padx=10, pady=5)
        self._message_row += 1
        self._scroll_to_bottom()

    def _remove_indicator(self):
        if self._indicator is not None:
            self._indicator.destroy()
            self._indicator = None
            self._message_row -= 1

    def _on_send_shortcut(self, _event):
        self.send()
        return "break"

    def send_message(self, message: str):
        if self._busy or not message.strip():
            return
        self._submit(message.strip(), "user")

    def send(self):
        if self._busy:
            return
        message = self.entry.get("1.0", "end").strip()
        if not message:
            return
        self.entry.delete("1.0", "end")
        self._submit(message, "user")

    def _submit(self, message: str, role: str):
        self._active_message = message
        self._append_message(role, message)
        self._show_indicator("JARVIS sta elaborando")
        self._set_busy(True)
        should_speak = bool(self._speak_enabled.get())

        def work():
            try:
                reply = self.handle_message(message)
                persisted = True
            except Exception as error:
                reply = f"Si è verificato un errore: {error}"
                persisted = False
            self._results.put(("reply", reply, persisted, should_speak and bool(self.speak)))
            if should_speak and self.speak:
                try:
                    self.speak(reply)
                except Exception as error:
                    print(f"Sintesi vocale non riuscita: {error}")
                finally:
                    self._results.put(("speech_done", "", False, False))

        threading.Thread(target=work, daemon=True).start()
        self.after(60, self._poll_result)

    def listen_once(self):
        if self._busy or not self.listen:
            return
        self._show_indicator("Microfono in ascolto")
        self._set_busy(True)

        def work():
            try:
                result = self.listen()
                self._results.put(("transcript", result, False, False))
            except Exception as error:
                self._results.put(("listen_error", str(error), False, False))

        threading.Thread(target=work, daemon=True).start()
        self.after(60, self._poll_result)

    def _poll_result(self):
        if not self.winfo_exists():
            return
        try:
            kind, value, persisted, speech_pending = self._results.get_nowait()
        except Empty:
            self.after(60, self._poll_result)
            return

        self._remove_indicator()
        if kind == "reply":
            if persisted:
                self._pending_echoes[("user", self._active_message)] += 1
                self._pending_echoes[("assistant", value)] += 1
            self._append_message("assistant", value)
            if persisted:
                self._read_external_history()
            if speech_pending:
                self._show_indicator("JARVIS sta parlando")
                self.after(60, self._poll_result)
            else:
                self._set_busy(False)
                self.entry.focus()
        elif kind == "speech_done":
            self._remove_indicator()
            self._set_busy(False)
            self.entry.focus()
        elif kind == "listen_error":
            self._append_message("assistant", f"Errore microfono: {value}")
            self._set_busy(False)
        elif not value:
            self._append_message("assistant", "Non ho sentito una richiesta. Riprova.")
            self._set_busy(False)
        else:
            self._set_busy(False)
            self._submit(value, "user")

    def _sync_external_history(self):
        if not self.winfo_exists():
            return
        if not self._busy and self.load_after_callback:
            self._read_external_history()
        self.after(900, self._sync_external_history)

    def _read_external_history(self):
        if not self.load_after_callback:
            return
        try:
            messages = self.load_after_callback(self._last_message_id)
            for message in messages:
                self._last_message_id = max(self._last_message_id, message["id"])
                echo = (message["role"], message["content"])
                if self._pending_echoes[echo]:
                    self._pending_echoes[echo] -= 1
                else:
                    self._append_message(
                        message["role"], message["content"], message.get("created_at")
                    )
        except Exception as error:
            print(f"Sincronizzazione cronologia non riuscita: {error}")

    def _set_busy(self, busy: bool):
        self._busy = busy
        state = "disabled" if busy else "normal"
        self.send_button.configure(state=state, text="ATTENDI…" if busy else "INVIA  →")
        self.voice_button.configure(state=state if self.listen else "disabled")

    def clear_history(self):
        if self._busy:
            return
        confirmed = messagebox.askyesno(
            "Cancella cronologia",
            "Vuoi cancellare la cronologia della conversazione? I fatti memorizzati resteranno salvati.",
            parent=self.winfo_toplevel(),
        )
        if not confirmed:
            return
        try:
            if self.clear_history_callback:
                self.clear_history_callback()
            for child in self.messages.winfo_children():
                child.destroy()
            self._message_row = 0
            self._pending_echoes.clear()
            self._append_message("assistant", "Cronologia cancellata. Memoria dei fatti conservata.")
        except Exception as error:
            self._append_message("assistant", f"Non sono riuscito a cancellare la cronologia: {error}")
