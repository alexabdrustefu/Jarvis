"""Operational dashboard with quick actions and a compact JARVIS HUD."""

import math
from datetime import datetime

import customtkinter as ctk


class DashboardView(ctk.CTkFrame):
    BG = "#080B12"
    PANEL = "#111722"
    BLUE = "#E36B35"
    CYAN = "#63DDF2"
    GOLD = "#F2B84B"
    TEXT = "#E6F1FF"
    MUTED = "#91A4BE"
    GREEN = "#34D399"

    QUICK_ACTIONS = (
        ("METEO", "Previsioni per oggi", "meteo oggi"),
        ("NOTIZIE", "Ultimi titoli", "dimmi le notizie"),
        ("SISTEMA", "Ora e stato", "che ore sono"),
    )

    def __init__(self, master, on_action):
        super().__init__(master, fg_color="transparent")
        self.on_action = on_action
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 18))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header, text="CENTRO DI COMANDO", font=("Segoe UI", 11, "bold"),
            text_color=self.CYAN,
        ).grid(row=0, column=0, sticky="w")
        self.clock = ctk.CTkLabel(
            header, text="", font=("Consolas", 13), text_color=self.MUTED,
        )
        self._clock_job = None
        self.clock.grid(row=0, column=1, sticky="e")
        self._update_clock()

        hero = ctk.CTkFrame(self, fg_color=self.PANEL, corner_radius=18)
        hero.grid(row=1, column=0, columnspan=2, sticky="ew", padx=2, pady=(0, 14))
        hero.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            hero, text="Buongiorno, Boss.", font=("Segoe UI", 27, "bold"),
            text_color=self.TEXT,
        ).grid(row=0, column=0, sticky="w", padx=(24, 10), pady=(22, 4))
        ctk.CTkLabel(
            hero,
            text="Interfaccia attiva. Qual è la prossima operazione?",
            font=("Segoe UI", 13), text_color=self.MUTED,
        ).grid(row=1, column=0, sticky="w", padx=(24, 10), pady=(0, 17))

        hud = ctk.CTkCanvas(
            hero, width=130, height=130, bg=self.PANEL, highlightthickness=0,
        )
        hud.grid(row=0, column=1, rowspan=2, padx=(4, 22), pady=10)
        self._draw_hud(hud)
        self._hud_angle = 0
        self._hud_pulse = 0
        self._hud_arc = hud.create_arc(
            17, 17, 113, 113, start=0, extent=78, style="arc",
            outline=self.CYAN, width=2,
        )
        self._hud_arc_inner = hud.create_arc(
            27, 27, 103, 103, start=180, extent=52, style="arc",
            outline="#38BDF8", width=1,
        )
        self._hud_glow = hud.create_oval(
            47, 47, 83, 83, outline="#38BDF8", width=1,
        )
        self._hud_orbit = hud.create_oval(0, 0, 0, 0, fill=self.GOLD, outline="")
        self._hud_canvas = hud
        self._hud_animation_id = None
        self._animate_hud()
        self.bind("<Destroy>", self._stop_hud_animation, add="+")

        actions_header = ctk.CTkFrame(self, fg_color="transparent")
        actions_header.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 5))
        ctk.CTkLabel(
            actions_header, text="AZIONI RAPIDE", font=("Segoe UI", 11, "bold"),
            text_color=self.MUTED,
        ).pack(side="left")
        ctk.CTkLabel(
            actions_header, text="SCEGLI UN MODULO", font=("Consolas", 10),
            text_color="#526681",
        ).pack(side="right")

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=3, column=0, columnspan=2, sticky="nsew")
        actions.grid_columnconfigure((0, 1), weight=1)
        for index, (tag, description, command) in enumerate(self.QUICK_ACTIONS):
            card = ctk.CTkFrame(actions, fg_color=self.PANEL, corner_radius=14)
            card.grid(row=index // 2, column=index % 2, padx=5, pady=5, sticky="nsew")
            card.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                card, text=tag, font=("Consolas", 11, "bold"), text_color=self.BLUE,
            ).grid(row=0, column=0, sticky="w", padx=16, pady=(13, 2))
            ctk.CTkLabel(
                card, text=description, font=("Segoe UI", 14, "bold"),
                text_color=self.TEXT,
            ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 12))
            ctk.CTkButton(
                card, text="ESEGUI  →", width=105, height=30, corner_radius=8,
                fg_color="#123149", hover_color="#174766", text_color=self.CYAN,
                font=("Consolas", 10, "bold"),
                command=lambda value=command: self.on_action(value),
            ).grid(row=0, column=1, rowspan=2, padx=14, pady=12)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ctk.CTkLabel(
            footer, text="●  CORE ONLINE", font=("Consolas", 10, "bold"),
            text_color=self.GREEN,
        ).pack(side="left")
        ctk.CTkLabel(
            footer, text="GROQ  ·  SQLITE  ·  WINDOWS", font=("Consolas", 9),
            text_color="#526681",
        ).pack(side="right")

    @staticmethod
    def _draw_hud(canvas):
        canvas.create_oval(13, 13, 117, 117, outline="#164765", width=1)
        canvas.create_oval(23, 23, 107, 107, outline="#1D3852", width=1)
        canvas.create_oval(35, 35, 95, 95, outline="#38BDF8", width=2)
        canvas.create_oval(43, 43, 87, 87, fill="#0B2033", outline="#67E8F9", width=1)
        canvas.create_text(65, 65, text="J", fill="#E6F1FF", font=("Segoe UI", 24, "bold"))
        for x, y in ((65, 8), (65, 122), (8, 65), (122, 65)):
            canvas.create_oval(x - 2, y - 2, x + 2, y + 2, fill="#67E8F9", outline="")

    def _update_clock(self):
        if not self.winfo_exists():
            return
        now = datetime.now()
        weekdays = ("lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica")
        months = ("gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre")
        date_text = f"{weekdays[now.weekday()]} {now.day} {months[now.month - 1]} {now.year}"
        self.clock.configure(text=f"{date_text}     {now:%H:%M:%S}")
        self._clock_job = self.after(1000, self._update_clock)

    def on_hide(self):
        for job_name in ("_hud_animation_id", "_clock_job"):
            job = getattr(self, job_name, None)
            if job is not None:
                try:
                    self.after_cancel(job)
                except Exception:
                    pass
                setattr(self, job_name, None)

    def on_show(self):
        if self._hud_animation_id is None:
            self._animate_hud()
        if self._clock_job is None:
            self._update_clock()

    def _animate_hud(self):
        if not self.winfo_exists():
            return
        self._hud_angle = (self._hud_angle + 7) % 360
        self._hud_pulse = (self._hud_pulse + 0.045) % (2 * math.pi)
        self._hud_canvas.itemconfigure(self._hud_arc, start=self._hud_angle)
        self._hud_canvas.itemconfigure(self._hud_arc_inner, start=(180 - self._hud_angle) % 360)
        inset = 7 + math.sin(self._hud_pulse) * 3
        self._hud_canvas.coords(self._hud_glow, 35 + inset, 35 + inset, 95 - inset, 95 - inset)
        orbit_angle = math.radians(self._hud_angle * 2)
        orbit_x = 65 + math.cos(orbit_angle) * 47
        orbit_y = 65 + math.sin(orbit_angle) * 47
        self._hud_canvas.coords(self._hud_orbit, orbit_x - 2.5, orbit_y - 2.5, orbit_x + 2.5, orbit_y + 2.5)
        self._hud_animation_id = self.after(30, self._animate_hud)

    def _stop_hud_animation(self, event):
        if event.widget is self and self._hud_animation_id is not None:
            try:
                self.after_cancel(self._hud_animation_id)
            except Exception:
                pass
