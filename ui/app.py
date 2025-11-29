import tkinter as tk
from tkinter import ttk

from config.constants import  THEMES, PIECE_SETS
from engine.chess_engine import  ChessEngine
from ui.gui import ChessGUI

# --- MAIN APP: START MENU + GAME -------------------------------------------


class ChessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Endgame Chess – AI Project")
        self.root.geometry("1100x720")
        self.root.minsize(1000, 680)

        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
        self.style.configure("Main.TFrame", background="#F5F5F5")

        self.start_frame = None
        self.game_gui = None

        self._show_start_menu()

    # ---------- START MENU --------------------------------------------------

    def _show_start_menu(self):
        if self.game_gui:
            self.game_gui.destroy()

        self.start_frame = ttk.Frame(self.root, style="Main.TFrame")
        self.start_frame.pack(fill="both", expand=True, padx=40, pady=40)

        # Title
        title = ttk.Label(
            self.start_frame,
            text="Endgame Chess",
            font=("Segoe UI", 26, "bold"),
            background="#F5F5F5",
        )
        title.pack(pady=(0, 10))

        subtitle = ttk.Label(
            self.start_frame,
            text="AI Group Project – Python UI/UX",
            font=("Segoe UI", 12),
            foreground="#555555",
            background="#F5F5F5",
        )
        subtitle.pack(pady=(0, 20))

        # Settings frame
        settings = ttk.Frame(self.start_frame, style="Main.TFrame")
        settings.pack(pady=10)

        # Time control
        time_row = ttk.Frame(settings, style="Main.TFrame")
        time_row.grid(row=0, column=0, sticky="w", pady=5)
        ttk.Label(
            time_row,
            text="Time per side (minutes):",
            font=("Segoe UI", 11),
            background="#F5F5F5",
        ).pack(side="left")
        self.time_var = tk.StringVar(value="5")
        ttk.Spinbox(
            time_row,
            from_=1,
            to=60,
            textvariable=self.time_var,
            width=5,
        ).pack(side="left", padx=(8, 0))

        # Theme selection
        theme_row = ttk.Frame(settings, style="Main.TFrame")
        theme_row.grid(row=1, column=0, sticky="w", pady=5)
        ttk.Label(
            theme_row,
            text="Board theme:",
            font=("Segoe UI", 11),
            background="#F5F5F5",
        ).pack(side="left")
        self.theme_var = tk.StringVar(value="Classic")
        ttk.Combobox(
            theme_row,
            textvariable=self.theme_var,
            values=list(THEMES.keys()),
            state="readonly",
            width=10,
        ).pack(side="left", padx=(8, 0))

        # Piece set selection
        piece_row = ttk.Frame(settings, style="Main.TFrame")
        piece_row.grid(row=2, column=0, sticky="w", pady=5)
        ttk.Label(
            piece_row,
            text="Piece style:",
            font=("Segoe UI", 11),
            background="#F5F5F5",
        ).pack(side="left")
        self.piece_set_var = tk.StringVar(value="Unicode")
        ttk.Combobox(
            piece_row,
            textvariable=self.piece_set_var,
            values=list(PIECE_SETS.keys()),
            state="readonly",
            width=10,
        ).pack(side="left", padx=(8, 0))

        # Buttons: modes
        btn_frame = ttk.Frame(self.start_frame, style="Main.TFrame")
        btn_frame.pack(pady=30)

        classic_btn = ttk.Button(
            btn_frame,
            text="Play Classic Chess",
            command=lambda: self._start_game(mode="classic"),
            width=22,
        )
        classic_btn.pack(pady=5)

        endgame_btn = ttk.Button(
            btn_frame,
            text="Play Endgame Mode",
            command=lambda: self._start_game(mode="endgame"),
            width=22,
        )
        endgame_btn.pack(pady=5)

        info = ttk.Label(
            self.start_frame,
            text="Endgame mode: special setups for KQ vs K etc.\n"
                 "AI search (minimax / alpha-beta / MCTS) will be plugged into the engine.",
            font=("Segoe UI", 9),
            foreground="#777777",
            background="#F5F5F5",
            justify="center",
        )
        info.pack(pady=(10, 0))

    def _start_game(self, mode: str):
        # parse time
        try:
            minutes = int(self.time_var.get())
            if minutes <= 0:
                minutes = 5
        except ValueError:
            minutes = 5

        theme = self.theme_var.get()
        if theme not in THEMES:
            theme = "Classic"

        piece_set_name = self.piece_set_var.get()
        if piece_set_name not in PIECE_SETS:
            piece_set_name = "Unicode"

        # remove menu
        if self.start_frame:
            self.start_frame.destroy()
            self.start_frame = None

        # launch game GUI
        self.game_gui = ChessGUI(
            self.root,
            initial_minutes=minutes,
            initial_theme=theme,
            piece_set_name=piece_set_name,
            mode=mode,
            back_to_menu_callback=self._show_start_menu,
        )
