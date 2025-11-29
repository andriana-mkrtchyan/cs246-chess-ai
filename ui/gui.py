import tkinter as tk
from tkinter import ttk

from config.constants import (
    BOARD_SIZE,
    SQUARE_SIZE,
    THEMES,
    PIECE_SETS,
)

from engine.chess_engine import ChessEngine

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


# --- GAME UI ---------------------------------------------------------------


class ChessGUI:
    def __init__(
        self,
        root,
        initial_minutes: int,
        initial_theme: str,
        piece_set_name: str,
        mode: str,
        back_to_menu_callback,
    ):
        self.root = root
        self.mode = mode
        self.back_to_menu_callback = back_to_menu_callback

        self.engine = ChessEngine()
        if mode == "endgame":
            self.engine.reset_to_endgame_position()
        else:
            self.engine.reset_to_start_position()

        self.theme_name = tk.StringVar(value=initial_theme)
        self.piece_set_name = tk.StringVar(value=piece_set_name)
        self.piece_symbols = PIECE_SETS[piece_set_name]

        self.selected_square = None
        self.legal_moves = []
        self.last_move = None

        # clocks
        self.initial_minutes = initial_minutes
        self.white_time = initial_minutes * 60
        self.black_time = initial_minutes * 60
        self.white_clock_var = tk.StringVar()
        self.black_clock_var = tk.StringVar()
        self.timer_running = True

        # status & material
        self.status_var = tk.StringVar(value=self.engine.get_status())
        self.material_var = tk.StringVar()
        self.white_caps_var = tk.StringVar()
        self.black_caps_var = tk.StringVar()

        # layout
        self.main_frame = ttk.Frame(self.root, style="Main.TFrame")
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        self._setup_style()
        self._build_layout()
        self._draw_board()
        self._update_clocks()
        self._update_material_and_captures()

        # start ticking
        self.root.after(1000, self._tick)

    def destroy(self):
        self.main_frame.destroy()

    # ---------- STYLE & LAYOUT ---------------------------------------------

    def _setup_style(self):
        style = ttk.Style()
        style.configure("Side.TFrame", background="#F5F5F5")
        style.configure(
            "Title.TLabel",
            font=("Segoe UI", 18, "bold"),
            background="#F5F5F5",
        )
        style.configure(
            "Subtitle.TLabel",
            font=("Segoe UI", 10),
            foreground="#555555",
            background="#F5F5F5",
        )
        style.configure(
            "Section.TLabel",
            font=("Segoe UI", 11, "bold"),
            background="#F5F5F5",
        )
        style.configure(
            "Status.TLabel", font=("Segoe UI", 12), background="#F5F5F5"
        )

    def _build_layout(self):
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=0)
        self.main_frame.rowconfigure(1, weight=1)

        # header
        header = ttk.Frame(self.main_frame, style="Main.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        title_text = "Endgame Chess – Classic Mode" if self.mode == "classic" \
            else "Endgame Chess – Endgame Mode"
        ttk.Label(
            header, text=title_text, style="Title.TLabel"
        ).pack(side="left")

        ttk.Button(
            header, text="Back to menu", command=self._back_to_menu
        ).pack(side="right")

        # board
        board_frame = ttk.Frame(self.main_frame, style="Main.TFrame")
        board_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 15))

        canvas_size = SQUARE_SIZE * BOARD_SIZE + 40
        self.canvas = tk.Canvas(
            board_frame,
            width=canvas_size,
            height=canvas_size,
            highlightthickness=0,
            bg="#F5F5F5",
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # side panel
        side_frame = ttk.Frame(self.main_frame, style="Side.TFrame")
        side_frame.grid(row=1, column=1, sticky="ns")

        # clocks
        clock_frame = ttk.Frame(side_frame, style="Side.TFrame")
        clock_frame.pack(fill="x", pady=(0, 8))
        clock_frame.columnconfigure(0, weight=1)
        clock_frame.columnconfigure(1, weight=1)

        ttk.Label(clock_frame, text="Black", style="Section.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            clock_frame,
            textvariable=self.black_clock_var,
            font=("Segoe UI", 12, "bold"),
            background="#F5F5F5",
        ).grid(row=0, column=1, sticky="e")

        ttk.Label(clock_frame, text="White", style="Section.TLabel").grid(
            row=1, column=0, sticky="w"
        )
        ttk.Label(
            clock_frame,
            textvariable=self.white_clock_var,
            font=("Segoe UI", 12, "bold"),
            background="#F5F5F5",
        ).grid(row=1, column=1, sticky="e")

        # status
        ttk.Label(
            side_frame, textvariable=self.status_var, style="Status.TLabel"
        ).pack(anchor="w", pady=(0, 8))

        # theme + pieces combobox (can still change in-game)
        theme_row = ttk.Frame(side_frame, style="Side.TFrame")
        theme_row.pack(fill="x", pady=(0, 5))
        ttk.Label(theme_row, text="Theme:", style="Section.TLabel").pack(
            side="left"
        )
        theme_cb = ttk.Combobox(
            theme_row,
            textvariable=self.theme_name,
            values=list(THEMES.keys()),
            state="readonly",
            width=10,
        )
        theme_cb.pack(side="left", padx=(5, 0))
        theme_cb.bind("<<ComboboxSelected>>", lambda e: self._draw_board())

        pieces_row = ttk.Frame(side_frame, style="Side.TFrame")
        pieces_row.pack(fill="x", pady=(0, 10))
        ttk.Label(
            pieces_row, text="Pieces:", style="Section.TLabel"
        ).pack(side="left")
        pieces_cb = ttk.Combobox(
            pieces_row,
            textvariable=self.piece_set_name,
            values=list(PIECE_SETS.keys()),
            state="readonly",
            width=10,
        )
        pieces_cb.pack(side="left", padx=(5, 0))
        pieces_cb.bind("<<ComboboxSelected>>", self._on_piece_set_change)

        # material & captures
        ttk.Label(
            side_frame, textvariable=self.material_var, style="Section.TLabel"
        ).pack(anchor="w", pady=(0, 4))

        cap_frame = ttk.Frame(side_frame, style="Side.TFrame")
        cap_frame.pack(fill="x", pady=(0, 10))
        cap_frame.columnconfigure(1, weight=1)

        ttk.Label(
            cap_frame, text="White captured:", style="Subtitle.TLabel"
        ).grid(row=0, column=0, sticky="w")
        self.white_caps_label = tk.Label(
            cap_frame,
            textvariable=self.white_caps_var,
            font=("Segoe UI Symbol", 14),
            bg="#F5F5F5",
        )
        self.white_caps_label.grid(row=0, column=1, sticky="w")

        ttk.Label(
            cap_frame, text="Black captured:", style="Subtitle.TLabel"
        ).grid(row=1, column=0, sticky="w")
        self.black_caps_label = tk.Label(
            cap_frame,
            textvariable=self.black_caps_var,
            font=("Segoe UI Symbol", 14),
            bg="#F5F5F5",
        )
        self.black_caps_label.grid(row=1, column=1, sticky="w")

        # buttons
        btn_frame = ttk.Frame(side_frame, style="Side.TFrame")
        btn_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(
            btn_frame, text="New Game", command=self.on_new_game
        ).pack(side="left", padx=(0, 5))
        ttk.Button(
            btn_frame, text="AI Move", command=self.on_ai_move
        ).pack(side="left")
        ttk.Button(
            btn_frame, text="Undo", command=self.on_undo
        ).pack(side="left", padx=(5, 0))

        # move log
        ttk.Label(
            side_frame, text="Move history", style="Section.TLabel"
        ).pack(anchor="w", pady=(10, 2))

        self.move_log = tk.Listbox(
            side_frame,
            height=22,
            width=32,
            font=("Consolas", 10),
            activestyle="none",
        )
        self.move_log.pack(fill="both", expand=True)

    # ---------- CLOCKS & MATERIAL ------------------------------------------

    def _format_time(self, seconds: int) -> str:
        m = seconds // 60
        s = seconds % 60
        return f"{m:02d}:{s:02d}"

    def _update_clocks(self):
        self.white_clock_var.set(self._format_time(self.white_time))
        self.black_clock_var.set(self._format_time(self.black_time))

    def _tick(self):
        if self.timer_running:
            # decrease the time for the side to move
            if self.engine.side_to_move() == "w":
                if self.white_time > 0:
                    self.white_time -= 1
            else:
                if self.black_time > 0:
                    self.black_time -= 1

            # check for time over
            if self.white_time == 0 or self.black_time == 0:
                self.timer_running = False

                # White's flag falls first
                if self.white_time == 0 and self.black_time > 0:
                    if self.engine.has_mating_material("b"):
                        self.status_var.set("White flagged • Black wins on time")
                    else:
                        self.status_var.set(
                            "Draw • White flagged but Black has insufficient material"
                        )

                # Black's flag falls first
                elif self.black_time == 0 and self.white_time > 0:
                    if self.engine.has_mating_material("w"):
                        self.status_var.set("Black flagged • White wins on time")
                    else:
                        self.status_var.set(
                            "Draw • Black flagged but White has insufficient material"
                        )

                # both out of time
                else:
                    self.status_var.set("Draw • Both sides out of time")

            # update the displayed clocks
            self._update_clocks()

        # keep calling _tick every second
        self.root.after(1000, self._tick)


    def _update_material_and_captures(self):
        score = self.engine.get_material_balance()
        if score > 0:
            self.material_var.set(f"Material: White +{score}")
        elif score < 0:
            self.material_var.set(f"Material: Black +{abs(score)}")
        else:
            self.material_var.set("Material: equal")

        white_caps, black_caps = self.engine.get_captures()
        self.white_caps_var.set(
            "".join(self.piece_symbols.get(p, "?") for p in white_caps)
        )
        self.black_caps_var.set(
            "".join(self.piece_symbols.get(p, "?") for p in black_caps)
        )

    # ---------- DRAWING -----------------------------------------------------

    def _current_colors(self):
        t = THEMES[self.theme_name.get()]
        return (
            t["light"],
            t["dark"],
            t["highlight"],
            t["selected"],
            t["last_move"],
        )

    def _draw_board(self):
        self.canvas.delete("all")
        board = self.engine.get_board()
        light, dark, highlight, selected_color, last_move_color = (
            self._current_colors()
        )
        offset = 20

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                x1 = offset + col * SQUARE_SIZE
                y1 = offset + row * SQUARE_SIZE
                x2 = x1 + SQUARE_SIZE
                y2 = y1 + SQUARE_SIZE

                color = light if (row + col) % 2 == 0 else dark

                if self.last_move:
                    (fr, fc), (tr, tc) = self.last_move
                    if (row, col) in [(fr, fc), (tr, tc)]:
                        color = last_move_color

                if self.selected_square == (row, col):
                    color = selected_color
                elif (row, col) in self.legal_moves:
                    color = highlight

                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=color, outline=""
                )

                piece = board[row][col]
                if piece:
                    symbol = self.piece_symbols.get(piece, "?")
                    font_size = 40 if self.piece_set_name.get() == "Unicode" else 30
                    self.canvas.create_text(
                        (x1 + x2) // 2,
                        (y1 + y2) // 2,
                        text=symbol,
                        font=("Segoe UI Symbol", font_size),
                    )

        # coordinate labels
        files = "abcdefgh"
        for col in range(BOARD_SIZE):
            file_char = files[col]
            x = offset + col * SQUARE_SIZE + SQUARE_SIZE / 2
            self.canvas.create_text(
                x,
                offset + BOARD_SIZE * SQUARE_SIZE + 12,
                text=file_char,
                font=("Segoe UI", 10),
                fill="#555555",
            )
            self.canvas.create_text(
                x,
                offset - 10,
                text=file_char,
                font=("Segoe UI", 10),
                fill="#555555",
            )

        for row in range(BOARD_SIZE):
            rank = str(BOARD_SIZE - row)
            y = offset + row * SQUARE_SIZE + SQUARE_SIZE / 2
            self.canvas.create_text(
                offset - 10,
                y,
                text=rank,
                font=("Segoe UI", 10),
                fill="#555555",
            )
            self.canvas.create_text(
                offset + BOARD_SIZE * SQUARE_SIZE + 10,
                y,
                text=rank,
                font=("Segoe UI", 10),
                fill="#555555",
            )

        self.status_var.set(self.engine.get_status())
        self._update_material_and_captures()

        if self.engine.is_game_over():
            self.timer_running = False

    # ---------- EVENTS ------------------------------------------------------


    def _coords_from_event(self, event):
        offset = 20
        col = (event.x - offset) // SQUARE_SIZE
        row = (event.y - offset) // SQUARE_SIZE
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            return row, col
        return None

    def on_canvas_click(self, event):
        if self.engine.is_game_over():
            return

        square = self._coords_from_event(event)
        if square is None:
            return

        row, col = square
        board = self.engine.get_board()
        piece = board[row][col]

        if self.selected_square is None:
            if piece and piece[0] == self.engine.side_to_move():
                self.selected_square = (row, col)
                self.legal_moves = self.engine.get_legal_moves_from(row, col)
            else:
                self.selected_square = None
                self.legal_moves = []
        else:
            if (row, col) == self.selected_square:
                self.selected_square = None
                self.legal_moves = []
            elif (row, col) in self.legal_moves:
                from_row, from_col = self.selected_square
                to_row, to_col = row, col
                notation = self.engine.make_move(
                    from_row, from_col, to_row, to_col
                )
                if notation is not None:
                    self.last_move = ((from_row, from_col), (to_row, to_col))
                    self._append_move_to_log(notation)
                self.selected_square = None
                self.legal_moves = []
            else:
                if piece and piece[0] == self.engine.side_to_move():
                    self.selected_square = (row, col)
                    self.legal_moves = self.engine.get_legal_moves_from(
                        row, col
                    )
                else:
                    self.selected_square = None
                    self.legal_moves = []

        self._draw_board()


    def _append_move_to_log(self, notation):
        move_index = len(self.engine.move_history)
        self.move_log.insert("end", f"{move_index}. {notation}")
        self.move_log.see("end")


    def on_new_game(self):
        if self.mode == "classic":
            self.engine.reset_to_start_position()
        else:
            self.engine.reset_to_endgame_position()

        self.selected_square = None
        self.legal_moves = []
        self.last_move = None
        self.move_log.delete(0, "end")

        self.white_time = self.initial_minutes * 60
        self.black_time = self.initial_minutes * 60
        self.timer_running = True
        self._update_clocks()
        self._draw_board()


    def on_undo(self):
        undone = self.engine.undo_last_move()
        if undone is None:
            return

        last_index = self.move_log.size() - 1
        if last_index >= 0:
            self.move_log.delete(last_index)

        # Clear highlight after undo
        self.last_move = None
        self.selected_square = None
        self.legal_moves = []
        self.timer_running = not self.engine.is_game_over()
        self._draw_board()


    def on_ai_move(self):
        """
        AI Move Button:
        - Calls engine.find_best_move(method=...)
        - Updates board, move log, highlights last move
        """
        if self.engine.is_game_over():
            self.status_var.set("Game over – no legal moves.")
            return

        # Choose the AI algorithm here.
        # Later you can connect this to a dropdown in the UI.
        ai_method = "alphabeta"   # options: "minimax", "alphabeta", "iddfs", "mcts"

        result = self.engine.find_best_move(method=ai_method)
        if result is None:
            self.status_var.set("AI has no move (game over or error).")
            return

        from_row, from_col, to_row, to_col, notation = result

        # store last move for highlight
        self.last_move = ((from_row, from_col), (to_row, to_col))

        # add move to log
        self._append_move_to_log(notation)

        # redraw board with updated state
        self._draw_board()


    def _on_piece_set_change(self, event=None):
        name = self.piece_set_name.get()
        if name not in PIECE_SETS:
            name = "Unicode"
            self.piece_set_name.set(name)
        self.piece_symbols = PIECE_SETS[name]
        self._draw_board()


    def _back_to_menu(self):
        self.timer_running = False
        self.main_frame.destroy()
        self.back_to_menu_callback()
