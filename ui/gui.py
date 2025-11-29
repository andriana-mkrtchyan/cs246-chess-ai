import tkinter as tk
from tkinter import ttk

from config.constants import (
    BOARD_SIZE,
    SQUARE_SIZE,
    PIECE_SETS,
    THEMES,
)
from engine.chess_engine import ChessEngine


class ChessGUI:
    """
    Game UI:
      - Draws the board with themes & piece styles
      - Handles clicks, legal-move highlighting and last-move highlight
      - Shows timers, material balance, captured pieces and move log
      - Supports Classic vs Endgame mode
      - Uses ChessEngine for all rules, check, mate, stalemate, etc.
    """

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

        # --- engine & position ---------------------------------------------
        self.engine = ChessEngine()
        if mode == "endgame":
            self.engine.reset_to_endgame_position()
        else:
            self.engine.reset_to_start_position()

        # --- UI state -------------------------------------------------------
        self.theme_name = tk.StringVar(value=initial_theme)
        self.piece_set_name = tk.StringVar(value=piece_set_name)
        self.piece_symbols = PIECE_SETS[self.piece_set_name.get()]

        self.selected_square = None      # (row, col) or None
        self.legal_moves = []            # list of (row, col)
        self.last_move = None            # ((from_row, from_col), (to_row, to_col))
        self.square_size = SQUARE_SIZE   # will be updated based on window size

        # --- clocks ---------------------------------------------------------
        self.initial_minutes = initial_minutes
        self.white_time = initial_minutes * 60
        self.black_time = initial_minutes * 60
        self.white_clock_var = tk.StringVar()
        self.black_clock_var = tk.StringVar()
        self.timer_running = True

        # --- status / material / captures ----------------------------------
        self.status_var = tk.StringVar(value=self.engine.get_status())
        self.material_var = tk.StringVar()
        self.white_caps_var = tk.StringVar()
        self.black_caps_var = tk.StringVar()

        # --- layout root frame ----------------------------------------------
        self.main_frame = ttk.Frame(self.root, style="Main.TFrame")
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        self._setup_style()
        self._build_layout()
        self._draw_board()
        self._update_clocks()
        self._update_material_and_captures()

        # start ticking the timer
        self.root.after(1000, self._tick)

    def destroy(self):
        self.main_frame.destroy()

    # ======================================================================
    # STYLE & LAYOUT
    # ======================================================================

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
            "Status.TLabel",
            font=("Segoe UI", 12),
            background="#F5F5F5",
        )

        # Highlight styles for whose turn it is
        style.configure(
            "PlayerOn.TLabel",
            font=("Segoe UI", 11, "bold"),
            foreground="#1E88E5",
            background="#F5F5F5",
        )
        style.configure(
            "PlayerOff.TLabel",
            font=("Segoe UI", 11),
            foreground="#777777",
            background="#F5F5F5",
        )

    def _build_layout(self):
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=0)
        self.main_frame.rowconfigure(1, weight=1)

        # ---- header --------------------------------------------------------
        header = ttk.Frame(self.main_frame, style="Main.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        title_text = (
            "Endgame Chess – Classic Mode"
            if self.mode == "classic"
            else "Endgame Chess – Endgame Mode"
        )
        ttk.Label(header, text=title_text, style="Title.TLabel").pack(side="left")

        ttk.Button(
            header,
            text="Back to menu",
            command=self._back_to_menu,
        ).pack(side="right")

        # ---- board frame ---------------------------------------------------
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
        self.canvas.bind("<Configure>", lambda e: self._draw_board())
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # ---- side panel ----------------------------------------------------
        side_frame = ttk.Frame(self.main_frame, style="Side.TFrame")
        side_frame.grid(row=1, column=1, sticky="ns")

        # clocks (player labels + time labels)
        clock_frame = ttk.Frame(side_frame, style="Side.TFrame")
        clock_frame.pack(fill="x", pady=(0, 8))
        clock_frame.columnconfigure(0, weight=1)
        clock_frame.columnconfigure(1, weight=1)

        self.black_player_label = ttk.Label(
            clock_frame, text="Black", style="PlayerOff.TLabel"
        )
        self.black_player_label.grid(row=0, column=0, sticky="w")

        self.white_player_label = ttk.Label(
            clock_frame, text="White", style="PlayerOn.TLabel"
        )
        self.white_player_label.grid(row=1, column=0, sticky="w")

        # NEW: visible clock values
        black_time_label = ttk.Label(
            clock_frame,
            textvariable=self.black_clock_var,
            style="Subtitle.TLabel",
        )
        black_time_label.grid(row=0, column=1, sticky="e")

        white_time_label = ttk.Label(
            clock_frame,
            textvariable=self.white_clock_var,
            style="Subtitle.TLabel",
        )
        white_time_label.grid(row=1, column=1, sticky="e")

        # status text (check/checkmate/etc.)
        ttk.Label(
            side_frame, textvariable=self.status_var, style="Status.TLabel"
        ).pack(anchor="w", pady=(0, 8))

        # theme & piece style selector (in-game)
        theme_row = ttk.Frame(side_frame, style="Side.TFrame")
        theme_row.pack(fill="x", pady=(0, 5))
        ttk.Label(theme_row, text="Theme:", style="Section.TLabel").pack(side="left")
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
        ttk.Label(pieces_row, text="Pieces:", style="Section.TLabel").pack(side="left")
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

        ttk.Button(btn_frame, text="New Game", command=self.on_new_game).pack(
            side="left", padx=(0, 5)
        )
        ttk.Button(btn_frame, text="AI Move", command=self.on_ai_move).pack(
            side="left"
        )
        ttk.Button(btn_frame, text="Undo", command=self.on_undo).pack(
            side="left", padx=(5, 0)
        )

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

    # ======================================================================
    # CLOCKS & MATERIAL
    # ======================================================================

    def _format_time(self, seconds: int) -> str:
        m = seconds // 60
        s = seconds % 60
        return f"{m:02d}:{s:02d}"

    def _update_clocks(self):
        self.white_clock_var.set(self._format_time(self.white_time))
        self.black_clock_var.set(self._format_time(self.black_time))

    def _tick(self):
        if self.timer_running:
            # decrease time for the side to move
            if self.engine.side_to_move() == "w":
                if self.white_time > 0:
                    self.white_time -= 1
            else:
                if self.black_time > 0:
                    self.black_time -= 1

            # time over?
            if self.white_time == 0 or self.black_time == 0:
                self.timer_running = False

                # White out of time
                if self.white_time == 0 and self.black_time > 0:
                    if self.engine.has_mating_material("b"):
                        self.status_var.set("White flagged • Black wins on time")
                    else:
                        self.status_var.set(
                            "Draw • White flagged but Black has insufficient material"
                        )

                # Black out of time
                elif self.black_time == 0 and self.white_time > 0:
                    if self.engine.has_mating_material("w"):
                        self.status_var.set("Black flagged • White wins on time")
                    else:
                        self.status_var.set(
                            "Draw • Black flagged but White has insufficient material"
                        )

                # both flags down
                else:
                    self.status_var.set("Draw • Both sides out of time")

            self._update_clocks()

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

    # ======================================================================
    # DRAWING
    # ======================================================================

    def _current_colors(self):
        theme = self.theme_name.get()
        t = THEMES.get(theme, THEMES["Classic"])
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
        light, dark, highlight, selected_color, last_move_color = self._current_colors()

        # dynamic sizing & centering
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = SQUARE_SIZE * BOARD_SIZE + 80
            canvas_height = SQUARE_SIZE * BOARD_SIZE + 80

        max_board = min(canvas_width, canvas_height) - 60
        max_board = max(max_board, 8 * 40)

        self.square_size = max_board // BOARD_SIZE
        board_pix = self.square_size * BOARD_SIZE

        offset_x = (canvas_width - board_pix) // 2
        offset_y = (canvas_height - board_pix) // 2
        label_margin = 18

        # king in check?
        in_check_rc = None
        try:
            if self.engine.board.is_check():
                king_sq = self.engine.board.king(self.engine.board.turn)
                if king_sq is not None:
                    in_check_rc = self.engine._square_to_rc(king_sq)
        except Exception:
            in_check_rc = None

        # outer border
        self.canvas.create_rectangle(
            offset_x - 2,
            offset_y - 2,
            offset_x + board_pix + 2,
            offset_y + board_pix + 2,
            outline="#333333",
            width=2,
        )

        # squares & pieces
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                x1 = offset_x + col * self.square_size
                y1 = offset_y + row * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size

                color = light if (row + col) % 2 == 0 else dark

                # last move highlight
                if self.last_move:
                    (fr, fc), (tr, tc) = self.last_move
                    if (row, col) in [(fr, fc), (tr, tc)]:
                        color = last_move_color

                # selected / legal moves
                if self.selected_square == (row, col):
                    color = selected_color
                elif (row, col) in self.legal_moves:
                    color = highlight

                # king in check – highest priority
                if in_check_rc is not None and (row, col) == in_check_rc:
                    color = "#FF6B6B"

                self.canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=color,
                    outline="",
                )

                piece = board[row][col]
                if piece:
                    symbol = self.piece_symbols.get(piece, "?")
                    base_factor = (
                        0.6 if self.piece_set_name.get() == "Unicode" else 0.5
                    )
                    font_size = max(18, int(self.square_size * base_factor))
                    self.canvas.create_text(
                        (x1 + x2) // 2,
                        (y1 + y2) // 2,
                        text=symbol,
                        font=("Segoe UI Symbol", font_size),
                    )

        # coordinate labels (files & ranks)
        files = "abcdefgh"
        for col in range(BOARD_SIZE):
            file_char = files[col]
            x = offset_x + col * self.square_size + self.square_size / 2
            self.canvas.create_text(
                x,
                offset_y + board_pix + label_margin,
                text=file_char,
                font=("Segoe UI", 10),
                fill="#555555",
            )
            self.canvas.create_text(
                x,
                offset_y - label_margin,
                text=file_char,
                font=("Segoe UI", 10),
                fill="#555555",
            )

        for row in range(BOARD_SIZE):
            rank = str(BOARD_SIZE - row)
            y = offset_y + row * self.square_size + self.square_size / 2
            self.canvas.create_text(
                offset_x - label_margin,
                y,
                text=rank,
                font=("Segoe UI", 10),
                fill="#555555",
            )
            self.canvas.create_text(
                offset_x + board_pix + label_margin,
                y,
                text=rank,
                font=("Segoe UI", 10),
                fill="#555555",
            )

        # status & material
        self.status_var.set(self.engine.get_status())
        self._update_material_and_captures()

        # whose turn highlight
        self._update_turn_highlight()

        if self.engine.is_game_over():
            self.timer_running = False

    # ======================================================================
    # INPUT HANDLING
    # ======================================================================

    def _coords_from_event(self, event):
        """Convert a canvas click to (row, col) with centering."""
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        board_pix = self.square_size * BOARD_SIZE
        offset_x = (canvas_width - board_pix) // 2
        offset_y = (canvas_height - board_pix) // 2

        col = (event.x - offset_x) // self.square_size
        row = (event.y - offset_y) // self.square_size

        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            return int(row), int(col)
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
            # first click – pick up own piece
            if piece and piece[0] == self.engine.side_to_move():
                self.selected_square = (row, col)
                self.legal_moves = self.engine.get_legal_moves_from(row, col)
            else:
                self.selected_square = None
                self.legal_moves = []
        else:
            # second click – move / reselect / cancel
            if (row, col) == self.selected_square:
                self.selected_square = None
                self.legal_moves = []
            elif (row, col) in self.legal_moves:
                from_row, from_col = self.selected_square
                to_row, to_col = row, col
                notation = self.engine.make_move(from_row, from_col, to_row, to_col)
                if notation is not None:
                    self.last_move = ((from_row, from_col), (to_row, to_col))
                    self._append_move_to_log(notation)
                self.selected_square = None
                self.legal_moves = []
            else:
                if piece and piece[0] == self.engine.side_to_move():
                    self.selected_square = (row, col)
                    self.legal_moves = self.engine.get_legal_moves_from(row, col)
                else:
                    self.selected_square = None
                    self.legal_moves = []

        self._draw_board()

    def _append_move_to_log(self, notation: str):
        move_index = len(self.engine.move_history)
        self.move_log.insert("end", f"{move_index}. {notation}")
        self.move_log.see("end")

    # ======================================================================
    # BUTTON HANDLERS
    # ======================================================================

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

        self.last_move = None
        self.selected_square = None
        self.legal_moves = []
        self.timer_running = not self.engine.is_game_over()
        self._draw_board()

    def on_ai_move(self):
        """
        Simple AI button – calls ChessEngine.find_best_move()
        (which your teammates can replace with minimax/alpha-beta/MCTS).
        """
        if self.engine.is_game_over():
            self.status_var.set("Game over – no legal moves.")
            return

        move = self.engine.find_best_move()
        if move is None:
            self.status_var.set("AI has no move (game over or error).")
            return

        from_row, from_col, to_row, to_col, notation = move
        self.last_move = ((from_row, from_col), (to_row, to_col))
        self._append_move_to_log(notation)
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

    def _update_turn_highlight(self):
        """Visually highlight which side is to move."""
        if self.engine.side_to_move() == "w":
            self.white_player_label.configure(style="PlayerOn.TLabel")
            self.black_player_label.configure(style="PlayerOff.TLabel")
        else:
            self.white_player_label.configure(style="PlayerOff.TLabel")
            self.black_player_label.configure(style="PlayerOn.TLabel")
