"""Desktop application shell and navigation."""

import customtkinter as ctk

from interface.voice_input import VoiceInput
from interface.voice_output import VoiceOutput
from composition import create_application
from gui.ui.chat_view import ChatView
from gui.ui.dashboard import DashboardView
from gui.ui.local_tools_view import LocalToolsView


class JarvisApp:
    BG = "#080B12"
    PANEL = "#111722"
    BLUE = "#E36B35"
    CYAN = "#63DDF2"
    TEXT = "#E6F1FF"
    MUTED = "#91A4BE"

    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        application = create_application()
        self.router = application.router
        self.voice_input = VoiceInput()
        self.voice_output = VoiceOutput()
        self.local_store = application.store
        preferences = self.local_store.get_preferences()
        self.voice_output.voice = preferences.get("voice", self.voice_output.voice)
        self.voice_output.rate = preferences.get("speech_rate", "+0%")
        self._page_views = {}
        self._active_page = None
        self.root = ctk.CTk()
        self.root.title("J.A.R.V.I.S. | Personal AI")
        self.root.geometry("1180x760")
        self.root.minsize(960, 640)
        self.root.configure(fg_color=self.BG)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self._build_layout()
        self.show_chat()
        self._start_fade_in()
        self._reminder_poll_id = self.root.after(1500, self._poll_reminders)

    def _build_layout(self) -> None:
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self.root, width=220, corner_radius=0, fg_color=self.PANEL)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(
            sidebar, text="J.A.R.V.I.S.", font=("Segoe UI", 27, "bold"), text_color=self.BLUE
        ).pack(pady=(35, 5))
        ctk.CTkLabel(
            sidebar, text="PERSONAL AI SYSTEM", font=("Segoe UI", 10), text_color=self.MUTED
        ).pack(pady=(0, 35))

        ctk.CTkLabel(
            sidebar, text="OPERATIONS", font=("Consolas", 9, "bold"),
            text_color="#526681", anchor="w",
        ).pack(fill="x", padx=19, pady=(0, 7))

        self.nav_buttons = {}
        for label, callback in (
            ("◈   Centro di comando", self.show_dashboard),
            ("⌁   Interfaccia JARVIS", self.show_chat),
            ("◷   Pianificazione", self.show_local_tools),
        ):
            button = ctk.CTkButton(
                sidebar,
                text=label,
                height=42,
                corner_radius=9,
                fg_color="transparent",
                hover_color="#1C2C44",
                text_color=self.TEXT,
                anchor="w",
                command=callback,
            )
            button.configure(
                text="▦   Centro di comando" if not self.nav_buttons else "◉   Interfaccia J.A.R.V.I.S."
            )
            button.pack(fill="x", padx=15, pady=4)
            self.nav_buttons[label] = button

        spacer = ctk.CTkFrame(sidebar, fg_color="transparent")
        spacer.pack(fill="both", expand=True)
        ctk.CTkFrame(sidebar, height=1, fg_color="#263B56").pack(fill="x", padx=17, pady=12)
        status = ctk.CTkFrame(sidebar, fg_color="transparent")
        status.pack(anchor="w", padx=19, pady=(0, 4))
        self.status_dot = ctk.CTkCanvas(
            status, width=12, height=12, bg=self.PANEL, highlightthickness=0,
        )
        self.status_dot.pack(side="left", padx=(0, 7))
        self.status_dot_id = self.status_dot.create_oval(
            2, 2, 10, 10, fill="#34D399", outline="",
        )
        ctk.CTkLabel(
            status, text="CORE ACTIVE", font=("Consolas", 10, "bold"),
            text_color="#34D399",
        ).pack(side="left")
        self._pulse_status()
        ctk.CTkLabel(
            sidebar, text="GROQ  /  LOCAL MEMORY", font=("Consolas", 8),
            text_color="#526681",
        ).pack(anchor="w", padx=19, pady=(0, 17))

        self.content = ctk.CTkFrame(self.root, fg_color=self.BG, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew", padx=25, pady=25)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

    def _show(self, page_name: str, view_factory) -> ctk.CTkFrame:
        if self._active_page == page_name:
            return self._page_views[page_name]
        if self._active_page is not None:
            current = self._page_views[self._active_page]
            if hasattr(current, "on_hide"):
                current.on_hide()
            current.grid_remove()

        view = self._page_views.get(page_name)
        if view is None:
            view = view_factory(self.content)
            self._page_views[page_name] = view
            view.grid(row=0, column=0, sticky="nsew")
        else:
            view.grid()
            if hasattr(view, "on_show"):
                view.on_show()
        self._active_page = page_name
        return view

    def show_dashboard(self) -> None:
        self._select_nav("◈   Centro di comando")
        self._show("dashboard", lambda parent: DashboardView(parent, self._run_quick_action))

    def _run_quick_action(self, command: str) -> None:
        self.show_chat(command)

    def show_local_tools(self) -> None:
        self._select_nav("◷   Pianificazione")
        self._show("local_tools", lambda parent: LocalToolsView(
            parent, self.local_store,
            on_command=lambda command: self.show_chat(command),
            microphone=self.voice_input.Microphone,
            router=self.router,
        ))

    def show_chat(self, initial_message: str | None = None) -> None:
        self._select_nav("⌁   Interfaccia JARVIS")
        chat = self._show(
            "chat",
            lambda parent: ChatView(
                parent,
                self.router.handle,
                listen=self.voice_input.listen,
                speak=self.voice_output.speak,
                clear_history=self.router.ai.clear_history,
                load_history=self.router.ai.memory.get_recent_messages_with_timestamps,
                load_after=self.router.ai.memory.get_messages_after_id,
                speak_enabled=self.local_store.get_preferences()["voice_replies"],
                on_speak_toggle=lambda enabled: self.local_store.set_preference("voice_replies", enabled),
            )
        )
        chat.set_speak_enabled(self.local_store.get_preferences()["voice_replies"])
        preferences = self.local_store.get_preferences()
        self.voice_output.voice = preferences.get("voice", self.voice_output.voice)
        self.voice_output.rate = preferences.get("speech_rate", "+0%")
        if initial_message:
            chat.send_message(initial_message)

    def run(self) -> None:
        self.root.mainloop()

    def close(self) -> None:
        # Stop repeating UI timers without waiting for in-flight network workers.
        for view in self._page_views.values():
            if hasattr(view, "on_close"):
                view.on_close()
            if hasattr(view, "on_hide"):
                view.on_hide()
        try:
            self.root.after_cancel(self._reminder_poll_id)
        except Exception:
            pass
        self.root.destroy()

    def _poll_reminders(self):
        if not self.root.winfo_exists():
            return
        try:
            for _ident, title, _when in self.local_store.take_due():
                popup = ctk.CTkToplevel(self.root)
                popup.title("Promemoria J.A.R.V.I.S.")
                popup.geometry("390x160")
                popup.attributes("-topmost", True)
                ctk.CTkLabel(popup, text="PROMEMORIA", font=("Consolas", 12, "bold"),
                             text_color=self.CYAN).pack(pady=(24, 6))
                ctk.CTkLabel(popup, text=title, font=("Segoe UI", 16), wraplength=340).pack(padx=18, pady=6)
                ctk.CTkButton(popup, text="OK", width=90, command=popup.destroy).pack(pady=9)
        except Exception as error:
            print(f"Notifica promemoria non riuscita: {error}")
        self._reminder_poll_id = self.root.after(5000, self._poll_reminders)

    def _select_nav(self, selected: str) -> None:
        for label, button in self.nav_buttons.items():
            active = label == selected
            button.configure(
                fg_color="#292018" if active else "transparent",
                text_color=self.CYAN if active else self.TEXT,
                border_width=1 if active else 0,
                border_color="#A9512D",
            )

    def _pulse_status(self):
        if not self.root.winfo_exists():
            return
        self._status_phase = getattr(self, "_status_phase", 0) + 1
        color = "#34D399" if self._status_phase % 2 else "#167A68"
        self.status_dot.itemconfigure(self.status_dot_id, fill=color)
        self.root.after(600, self._pulse_status)

    def _start_fade_in(self):
        try:
            self.root.attributes("-alpha", 0.0)
        except Exception:
            return
        self._fade_step(0.0)

    def _fade_step(self, alpha: float):
        if not self.root.winfo_exists():
            return
        alpha = min(1.0, alpha + 0.08)
        self.root.attributes("-alpha", alpha)
        if alpha < 1.0:
            self.root.after(18, lambda: self._fade_step(alpha))
