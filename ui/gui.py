import tkinter as tk
from tkinter import ttk
from engine.chess_engine import ChessEngine
import chess

from ai.search_algorithms import (
    minimax,
    alpha_beta,
    mcts,
    iddfs_alphabeta_move,
)



# --- CONFIG -----------------------------------------------------------------

BOARD_SIZE = 8
SQUARE_SIZE = 80

ALGORITHMS = ["Minimax", "Alpha-Beta", "MCTS", "IDDFS"]

PIECE_SETS = {
    "Unicode": {
        "wK": "♔", "wQ": "♕", "wR": "♖", "wB": "♗", "wN": "♘", "wP": "♙",
        "bK": "♚", "bQ": "♛", "bR": "♜", "bB": "♝", "bN": "♞", "bP": "♟",
    },
    "Letters": {
        "wK": "K", "wQ": "Q", "wR": "R", "wB": "B", "wN": "N", "wP": "P",
        "bK": "k", "bQ": "q", "bR": "r", "bB": "b", "bN": "n", "bP": "p",
    },
}

PIECE_VALUES = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 0}

THEMES = {
    "Classic": {
        "light": "#EEEED2",
        "dark": "#769656",
        "highlight": "#BACA44",
        "selected": "#F6F669",
        "last_move": "#F3E99F",
    },
    "Dark": {
        "light": "#B0B0B0",
        "dark": "#404040",
        "highlight": "#6D8F1F",
        "selected": "#D4D24C",
        "last_move": "#595959",
    },
    "Ocean": {
        "light": "#E6F4F1",
        "dark": "#2F6F7E",
        "highlight": "#4BA3C3",
        "selected": "#8ED8F4",
        "last_move": "#71BFD8",
    },
"Candy": {
        "light": "#FFE4F9",
        "dark": "#C475ED",
        "highlight": "#F9A8D4",
        "selected": "#FDE68A",
        "last_move": "#FBCFE8",
    },

    # NEW: warm sunset theme (cream + red-brown)
    "Sunset": {
        "light": "#FDEBD0",   # soft cream
        "dark":  "#C4563F",   # terracotta
        "highlight": "#F5CBA7",
        "selected": "#F9E79F",
        "last_move": "#FAD7A0",
    },

    # NEW: galaxy theme (dark + neon blue)
    "Galaxy": {
        "light": "#2F3640",   # dark gray-blue
        "dark":  "#192A56",   # deep navy
        "highlight": "#00A8FF",
        "selected": "#9C88FF",
        "last_move": "#273C75",
    },
}




# --- ENGINE STUB -----------------------------------------------------------


class ChessEngineStub:
    def __init__(self):
        self.reset_to_start_position()

    def reset_to_start_position(self):
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bP"] * 8,
            [""] * 8,
            [""] * 8,
            [""] * 8,
            [""] * 8,
            ["wP"] * 8,
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"],
        ]
        self.white_to_move = True
        self.move_history = []
        self.move_stack = []
        self.white_captures = []
        self.black_captures = []

    def reset_to_endgame_position(self):
        # Simple KQ vs K placeholder
        self.board = [[""] * 8 for _ in range(8)]
        self.board[7][4] = "wK"
        self.board[5][4] = "wQ"
        self.board[0][4] = "bK"

        self.white_to_move = True
        self.move_history = []
        self.move_stack = []
        self.white_captures = []
        self.black_captures = []

    def side_to_move(self):
        return "w" if self.white_to_move else "b"

    def get_board(self):
        return self.board

    def _in_bounds(self, r, c):
        return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

    def _color_of(self, piece):
        return piece[0] if piece else None

    # ---------- helpers for python-chess ---------------------------------

    def _to_chess_board(self):
        """Convert our 2D board into a python-chess Board."""
        board = chess.Board.empty()
        # our row 0 is rank 8, row 7 is rank 1
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board[row][col]
                if not piece:
                    continue
                color = chess.WHITE if piece[0] == "w" else chess.BLACK
                ptype = piece[1]

                piece_type = {
                    "P": chess.PAWN,
                    "N": chess.KNIGHT,
                    "B": chess.BISHOP,
                    "R": chess.ROOK,
                    "Q": chess.QUEEN,
                    "K": chess.KING,
                }[ptype]

                file_ = col              # a-file = 0, h-file = 7
                rank_ = 7 - row          # row 0 -> rank 7 (8th rank)
                sq = chess.square(file_, rank_)
                board.set_piece_at(sq, chess.Piece(piece_type, color))

        board.turn = chess.WHITE if self.white_to_move else chess.BLACK
        return board

    def get_legal_moves_from(self, row, col):
        """
        Use python-chess to generate legal moves for the piece on (row, col).
        Returns a list of (to_row, to_col).
        """
        board = self._to_chess_board()

        from_file = col
        from_rank = 7 - row
        from_sq = chess.square(from_file, from_rank)

        moves = []
        for move in board.legal_moves:
            if move.from_square != from_sq:
                continue
            to_file = chess.square_file(move.to_square)
            to_rank = chess.square_rank(move.to_square)
            to_row = 7 - to_rank
            to_col = to_file
            moves.append((to_row, to_col))
        return moves

    def make_move(self, from_row, from_col, to_row, to_col):
        piece = self.board[from_row][from_col]
        captured = self.board[to_row][to_col]
        color = piece[0]

        self.move_stack.append(
            (from_row, from_col, to_row, to_col, piece, captured, self.white_to_move)
        )

        if captured:
            if color == "w":
                self.white_captures.append(captured)
            else:
                self.black_captures.append(captured)

        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = ""
        self.white_to_move = not self.white_to_move

        move_notation = (
            f"{piece}@{chr(from_col + ord('a'))}{BOARD_SIZE - from_row}"
            f"-{chr(to_col + ord('a'))}{BOARD_SIZE - to_row}"
        )
        if captured:
            move_notation += f" x{captured}"
        self.move_history.append(move_notation)
        return move_notation

    def undo_last_move(self):
        if not self.move_stack:
            return None

        fr, fc, tr, tc, piece, captured, prev_wtm = self.move_stack.pop()
        self.board[fr][fc] = piece
        self.board[tr][tc] = captured
        self.white_to_move = prev_wtm

        if captured:
            if piece[0] == "w":
                if self.white_captures:
                    self.white_captures.pop()
            else:
                if self.black_captures:
                    self.black_captures.pop()

        undone = self.move_history.pop() if self.move_history else None
        return undone

    def get_status(self):
        return "White to move" if self.white_to_move else "Black to move"

    def get_captures(self):
        return self.white_captures, self.black_captures

    def get_material_balance(self):
        score = 0
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                p = self.board[r][c]
                if p:
                    val = PIECE_VALUES.get(p[1], 0)
                    score += val if p[0] == "w" else -val
        return score

    def find_best_move(self, algo_name: str, depth: int):
        """
        Use real search algorithms (Minimax / Alpha-Beta / MCTS / Random)
        on a python-chess board, and return coordinates in our 2D board:
        (from_row, from_col, to_row, to_col)
        """
        board = self._to_chess_board()

        if board.is_game_over():
            return None

        maximizing = (board.turn == chess.WHITE)

        # --- choose algorithm ---
        if algo_name == "Minimax":
            _, best_move = minimax(board, depth, maximizing)

        elif algo_name == "Alpha-Beta":
            _, best_move = alpha_beta(
                board,
                depth,
                -float("inf"),
                float("inf"),
                maximizing,
            )

        elif algo_name == "MCTS":
            best_move = mcts(board, simulations=200)

        elif algo_name == "Random":
            legal = list(board.legal_moves)
            best_move = random.choice(legal) if legal else None

        else:
            # fallback – random
            legal = list(board.legal_moves)
            best_move = random.choice(legal) if legal else None

        if best_move is None:
            return None

        # convert python-chess squares back to (row, col) on our board
        from_file = chess.square_file(best_move.from_square)
        from_rank = chess.square_rank(best_move.from_square)
        to_file = chess.square_file(best_move.to_square)
        to_rank = chess.square_rank(best_move.to_square)

        from_row = 7 - from_rank
        from_col = from_file
        to_row = 7 - to_rank
        to_col = to_file

        return from_row, from_col, to_row, to_col



# --- APP WITH START MENU ----------------------------------------------------


class ChessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Endgame Chess – AI Project")
        self.root.geometry("1100x720")
        self.root.minsize(1000, 680)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Main.TFrame", background="#F5F5F5")

        self.start_frame = None
        self.game_gui = None

        self._build_start_menu()

    def _build_start_menu(self):
        if self.game_gui:
            self.game_gui.destroy()
            self.game_gui = None

        self.start_frame = ttk.Frame(self.root, style="Main.TFrame")
        self.start_frame.pack(fill="both", expand=True, padx=40, pady=40)

        # Header
        title = ttk.Label(
            self.start_frame,
            text="Endgame Chess",
            font=("Segoe UI", 26, "bold"),
            background="#F5F5F5",
        )
        title.pack(pady=(0, 5))

        subtitle = ttk.Label(
            self.start_frame,
            text="AI Group Project – Python UI/UX",
            font=("Segoe UI", 12),
            foreground="#555555",
            background="#F5F5F5",
        )
        subtitle.pack(pady=(0, 20))

        # Center card
        center = ttk.Frame(self.start_frame, style="Main.TFrame")
        center.pack(expand=True)

        # --- General settings (time/theme/pieces) -------------------------
        general = ttk.Frame(center, style="Main.TFrame")
        general.pack(pady=10)

        self.time_var = tk.StringVar(value="5")
        time_row = ttk.Frame(general, style="Main.TFrame")
        time_row.grid(row=0, column=0, sticky="w", pady=4)
        ttk.Label(
            time_row, text="Time per side (minutes):",
            font=("Segoe UI", 11), background="#F5F5F5",
        ).pack(side="left")
        ttk.Spinbox(
            time_row, from_=1, to=60,
            textvariable=self.time_var, width=5,
        ).pack(side="left", padx=(8, 0))

        self.theme_var = tk.StringVar(value="Classic")
        theme_row = ttk.Frame(general, style="Main.TFrame")
        theme_row.grid(row=1, column=0, sticky="w", pady=4)
        ttk.Label(
            theme_row, text="Board theme:",
            font=("Segoe UI", 11), background="#F5F5F5",
        ).pack(side="left")
        ttk.Combobox(
            theme_row,
            textvariable=self.theme_var,
            values=list(THEMES.keys()),
            state="readonly",
            width=10,
        ).pack(side="left", padx=(8, 0))

        self.piece_set_var = tk.StringVar(value="Unicode")
        piece_row = ttk.Frame(general, style="Main.TFrame")
        piece_row.grid(row=2, column=0, sticky="w", pady=4)
        ttk.Label(
            piece_row, text="Piece style:",
            font=("Segoe UI", 11), background="#F5F5F5",
        ).pack(side="left")
        ttk.Combobox(
            piece_row,
            textvariable=self.piece_set_var,
            values=list(PIECE_SETS.keys()),
            state="readonly",
            width=10,
        ).pack(side="left", padx=(8, 0))

        # --- Game type ----------------------------------------------------
        self.game_type_var = tk.StringVar(value="HvH")
        ttk.Label(
            center,
            text="Game type",
            font=("Segoe UI", 11, "bold"),
            background="#F5F5F5",
        ).pack(pady=(12, 4))
        game_type_frame = ttk.Frame(center, style="Main.TFrame")
        game_type_frame.pack()

        for text, value in [
            ("Human vs Human", "HvH"),
            ("Human vs AI", "HvAI"),
            ("AI vs AI", "AIvAI"),
        ]:
            ttk.Radiobutton(
                game_type_frame,
                text=text,
                value=value,
                variable=self.game_type_var,
                command=self._on_game_type_change,
            ).pack(anchor="w")

        # --- Mode (classic / endgame) ------------------------------------
        self.mode_var = tk.StringVar(value="classic")
        ttk.Label(
            center,
            text="Mode",
            font=("Segoe UI", 11, "bold"),
            background="#F5F5F5",
        ).pack(pady=(12, 4))
        mode_frame = ttk.Frame(center, style="Main.TFrame")
        mode_frame.pack()
        self.classic_rb = ttk.Radiobutton(
            mode_frame,
            text="Classic chess (full board)",
            value="classic",
            variable=self.mode_var,
        )
        self.classic_rb.pack(anchor="w")
        self.endgame_rb = ttk.Radiobutton(
            mode_frame,
            text="Endgame mode (custom positions)",
            value="endgame",
            variable=self.mode_var,
        )
        self.endgame_rb.pack(anchor="w")

        # --- AI settings --------------------------------------------------
        ttk.Label(
            center,
            text="AI settings",
            font=("Segoe UI", 11, "bold"),
            background="#F5F5F5",
        ).pack(pady=(14, 4))
        self.ai_settings_frame = ttk.Frame(center, style="Main.TFrame")
        self.ai_settings_frame.pack()

        # shared vars
        self.ai1_algo_var = tk.StringVar(value=ALGORITHMS[1])
        self.ai1_depth_var = tk.StringVar(value="3")
        self.ai2_algo_var = tk.StringVar(value=ALGORITHMS[0])
        self.ai2_depth_var = tk.StringVar(value="3")

        # HvAI settings
        self.hvai_frame = ttk.Frame(self.ai_settings_frame, style="Main.TFrame")
        ttk.Label(
            self.hvai_frame,
            text="AI algorithm:",
            font=("Segoe UI", 11),
            background="#F5F5F5",
        ).grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            self.hvai_frame,
            textvariable=self.ai1_algo_var,
            values=ALGORITHMS,
            state="readonly",
            width=12,
        ).grid(row=0, column=1, padx=(5, 15))
        ttk.Label(
            self.hvai_frame,
            text="Depth:",
            font=("Segoe UI", 11),
            background="#F5F5F5",
        ).grid(row=0, column=2, sticky="w")
        ttk.Spinbox(
            self.hvai_frame,
            from_=1,
            to=10,
            textvariable=self.ai1_depth_var,
            width=4,
        ).grid(row=0, column=3, padx=(5, 0))

        # AIvAI settings
        self.ava_frame = ttk.Frame(self.ai_settings_frame, style="Main.TFrame")
        ttk.Label(
            self.ava_frame,
            text="AI 1 (White):",
            font=("Segoe UI", 11, "bold"),
            background="#F5F5F5",
        ).grid(row=0, column=0, sticky="w", pady=(0, 2))
        ttk.Combobox(
            self.ava_frame,
            textvariable=self.ai1_algo_var,
            values=ALGORITHMS,
            state="readonly",
            width=12,
        ).grid(row=0, column=1, padx=(5, 15))
        ttk.Label(
            self.ava_frame,
            text="Depth:",
            font=("Segoe UI", 11),
            background="#F5F5F5",
        ).grid(row=0, column=2, sticky="w")
        ttk.Spinbox(
            self.ava_frame,
            from_=1,
            to=10,
            textvariable=self.ai1_depth_var,
            width=4,
        ).grid(row=0, column=3, padx=(5, 0))

        ttk.Label(
            self.ava_frame,
            text="AI 2 (Black):",
            font=("Segoe UI", 11, "bold"),
            background="#F5F5F5",
        ).grid(row=1, column=0, sticky="w", pady=(8, 2))
        ttk.Combobox(
            self.ava_frame,
            textvariable=self.ai2_algo_var,
            values=ALGORITHMS,
            state="readonly",
            width=12,
        ).grid(row=1, column=1, padx=(5, 15))
        ttk.Label(
            self.ava_frame,
            text="Depth:",
            font=("Segoe UI", 11),
            background="#F5F5F5",
        ).grid(row=1, column=2, sticky="w")
        ttk.Spinbox(
            self.ava_frame,
            from_=1,
            to=10,
            textvariable=self.ai2_depth_var,
            width=4,
        ).grid(row=1, column=3, padx=(5, 0))

        # initial state
        self._on_game_type_change()

        # Play button
        play_btn = ttk.Button(
            center,
            text="PLAY",
            command=self._start_game_from_menu,
            width=20,
        )
        play_btn.pack(pady=18)

        # Info
        # Info
        info = ttk.Label(
            self.start_frame,
            text=(
                "Use this screen to choose time control, mode, and AI settings.\n"
                "AI algorithms (Minimax / Alpha-Beta / MCTS / Random) run in Human vs AI and AI vs AI modes.\n"
                "In Human vs AI mode, press the 'AI Move' button for the AI to make its move."
            ),
            font=("Segoe UI", 9),
            foreground="#777777",
            background="#F5F5F5",
            justify="center",
        )
        info.pack(pady=(5, 0))



    def _on_game_type_change(self):
        gt = self.game_type_var.get()

        # clear AI settings frame
        for child in self.ai_settings_frame.winfo_children():
            child.pack_forget()
            child.grid_forget()

        if gt == "HvH":
            # no AI settings
            self.classic_rb.configure(state="normal")
            self.endgame_rb.configure(state="normal")
        elif gt == "HvAI":
            self.hvai_frame.pack(anchor="w")
            self.classic_rb.configure(state="normal")
            self.endgame_rb.configure(state="normal")
        elif gt == "AIvAI":
            self.ava_frame.pack(anchor="w")
            self.mode_var.set("endgame")
            self.classic_rb.configure(state="disabled")
            self.endgame_rb.configure(state="normal")

    def _start_game_from_menu(self):
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

        game_type = self.game_type_var.get()
        mode = self.mode_var.get()

        config = {
            "game_type": game_type,
            "mode": mode,
            "minutes": minutes,
            "theme": theme,
            "piece_set": piece_set_name,
            "ai1_algo": self.ai1_algo_var.get(),
            "ai1_depth": int(self.ai1_depth_var.get() or 1),
            "ai2_algo": self.ai2_algo_var.get(),
            "ai2_depth": int(self.ai2_depth_var.get() or 1),
            "ai_side": "b",
        }

        if self.start_frame:
            self.start_frame.destroy()
            self.start_frame = None

        self.game_gui = ChessGUI(self.root, config, back_to_menu_callback=self._build_start_menu)


class ChessGUI:
    def __init__(self, root, config, back_to_menu_callback):
        self.root = root
        self.config = config
        self.back_to_menu_callback = back_to_menu_callback

        # ----- engine setup -----
        self.engine = ChessEngine()
        if self.config["mode"] == "endgame":
            self.engine.reset_to_endgame_position()
        else:
            self.engine.reset_to_start_position()

        # ----- UI state -----
        self.theme_name = tk.StringVar(value=self.config["theme"])
        self.piece_set_name = tk.StringVar(value=self.config["piece_set"])
        self.piece_symbols = PIECE_SETS[self.piece_set_name.get()]

        self.selected_square = None
        self.legal_moves = []
        self.last_move = None

        self.initial_minutes = self.config["minutes"]
        self.white_time = self.initial_minutes * 60
        self.black_time = self.initial_minutes * 60
        self.white_clock_var = tk.StringVar()
        self.black_clock_var = tk.StringVar()
        self.timer_running = True

        self.status_var = tk.StringVar(value=self.engine.get_status())
        self.material_var = tk.StringVar()
        self.white_caps_var = tk.StringVar()
        self.black_caps_var = tk.StringVar()
        self.mode_info_var = tk.StringVar()

        # ----- root frame -----
        self.main_frame = ttk.Frame(self.root, style="Main.TFrame")
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        self._setup_style()
        self._build_layout()
        self._draw_board()
        self._update_clocks()
        self._update_material_and_captures()
        self._update_mode_label()

        self.root.after(1000, self._tick)

    def destroy(self):
        self.main_frame.destroy()

    # ------------------------------------------------------------------
    #  STYLING + LAYOUT
    # ------------------------------------------------------------------

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

    def _build_layout(self):
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=0)
        self.main_frame.rowconfigure(1, weight=1)

        # ----- header -----
        header = ttk.Frame(self.main_frame, style="Main.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        mode_text = (
            "Classic Mode" if self.config["mode"] == "classic" else "Endgame Mode"
        )
        ttk.Label(
            header,
            text=f"Endgame Chess – {mode_text}",
            style="Title.TLabel",
        ).pack(side="left")

        ttk.Button(
            header,
            text="Back to menu",
            command=self._back_to_menu,
        ).pack(side="right")

        # ----- board frame -----
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

        # ----- side bar -----
        side_frame = ttk.Frame(self.main_frame, style="Side.TFrame")
        side_frame.grid(row=1, column=1, sticky="ns")

        ttk.Label(
            side_frame,
            textvariable=self.mode_info_var,
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(0, 8))

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

        ttk.Label(
            side_frame,
            textvariable=self.status_var,
            style="Status.TLabel",
        ).pack(anchor="w", pady=(0, 8))

        # theme & pieces
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

        ttk.Label(
            side_frame,
            textvariable=self.material_var,
            style="Section.TLabel",
        ).pack(anchor="w", pady=(0, 4))

        # captures
        cap_frame = ttk.Frame(side_frame, style="Side.TFrame")
        cap_frame.pack(fill="x", pady=(0, 10))
        cap_frame.columnconfigure(1, weight=1)

        ttk.Label(
            cap_frame, text="White captured:", style="Subtitle.TLabel"
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            cap_frame,
            textvariable=self.white_caps_var,
            font=("Segoe UI Symbol", 14),
            bg="#F5F5F5",
        ).grid(row=0, column=1, sticky="w")

        ttk.Label(
            cap_frame, text="Black captured:", style="Subtitle.TLabel"
        ).grid(row=1, column=0, sticky="w")
        tk.Label(
            cap_frame,
            textvariable=self.black_caps_var,
            font=("Segoe UI Symbol", 14),
            bg="#F5F5F5",
        ).grid(row=1, column=1, sticky="w")

        # control buttons
        btn_frame = ttk.Frame(side_frame, style="Side.TFrame")
        btn_frame.pack(fill="x", pady=(0, 10))
        ttk.Button(btn_frame, text="New Game", command=self.on_new_game).pack(
            side="left", padx=(0, 5)
        )
        ttk.Button(btn_frame, text="AI Move", command=self.on_ai_move).pack(side="left")
        ttk.Button(btn_frame, text="Undo", command=self.on_undo).pack(
            side="left", padx=(5, 0)
        )

        ttk.Label(
            side_frame,
            text="Move history",
            style="Section.TLabel",
        ).pack(anchor="w", pady=(10, 2))
        self.move_log = tk.Listbox(
            side_frame,
            height=22,
            width=32,
            font=("Consolas", 10),
            activestyle="none",
        )
        self.move_log.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    #  MODE / CLOCK / MATERIAL
    # ------------------------------------------------------------------

    def _update_mode_label(self):
        gt = self.config["game_type"]
        mode = self.config["mode"]
        if gt == "HvH":
            text = f"Human vs Human • {mode.capitalize()} chess"
        elif gt == "HvAI":
            text = (
                f"Human vs AI • {mode.capitalize()} chess • "
                f"AI: {self.config['ai1_algo']} (depth {self.config['ai1_depth']})"
            )
        else:
            text = (
                f"AI vs AI • Endgame • "
                f"AI1: {self.config['ai1_algo']} (d{self.config['ai1_depth']}), "
                f"AI2: {self.config['ai2_algo']} (d{self.config['ai2_depth']})"
            )
        self.mode_info_var.set(text)

    def _format_time(self, seconds: int) -> str:
        m = seconds // 60
        s = seconds % 60
        return f"{m:02d}:{s:02d}"

    def _update_clocks(self):
        self.white_clock_var.set(self._format_time(self.white_time))
        self.black_clock_var.set(self._format_time(self.black_time))

    def _tick(self):
        if self.timer_running:
            if self.engine.side_to_move() == "w":
                if self.white_time > 0:
                    self.white_time -= 1
            else:
                if self.black_time > 0:
                    self.black_time -= 1

            if self.white_time == 0 or self.black_time == 0:
                self.timer_running = False
                if self.white_time == 0 and self.black_time > 0:
                    self.status_var.set("White flagged • Black wins on time")
                elif self.black_time == 0 and self.white_time > 0:
                    self.status_var.set("Black flagged • White wins on time")
                else:
                    self.status_var.set("Both out of time")

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

    # ------------------------------------------------------------------
    #  DRAWING
    # ------------------------------------------------------------------

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
                    font_size = 40 if self.piece_set_name.get() == "Unicode" else 30
                    self.canvas.create_text(
                        (x1 + x2) // 2,
                        (y1 + y2) // 2,
                        text=symbol,
                        font=("Segoe UI Symbol", font_size),
                    )

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

    # ------------------------------------------------------------------
    #  EVENTS / BUTTONS
    # ------------------------------------------------------------------

    def _coords_from_event(self, event):
        offset = 20
        col = (event.x - offset) // SQUARE_SIZE
        row = (event.y - offset) // SQUARE_SIZE
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            return row, col
        return None

    def on_canvas_click(self, event):
        gt = self.config["game_type"]

        # 1) AI vs AI -> board is only for viewing, no human input
        if gt == "AIvAI":
            self.status_var.set("AI vs AI mode: use 'AI Move' button to advance the game.")
            return

        square = self._coords_from_event(event)
        if square is None:
            return

        row, col = square
        board = self.engine.get_board()
        piece = board[row][col]

        # 2) Human vs AI -> allow clicks ONLY when it's the human's turn
        if gt == "HvAI":
            ai_side = self.config.get("ai_side", "b")  # default AI = Black
            human_side = "w" if ai_side == "b" else "b"

            if self.engine.side_to_move() != human_side:
                # it's AI's turn, user shouldn't move
                self.status_var.set("It's AI's turn – wait for AI to move.")
                return

        # 3) Normal selection / move logic
        if self.selected_square is None:
            # select only current side-to-move piece
            if piece and piece[0] == self.engine.side_to_move():
                self.selected_square = (row, col)
                self.legal_moves = self.engine.get_legal_moves_from(row, col)
            else:
                self.selected_square = None
                self.legal_moves = []
        else:
            if (row, col) == self.selected_square:
                # deselect
                self.selected_square = None
                self.legal_moves = []
            elif (row, col) in self.legal_moves:
                # make the human move
                from_row, from_col = self.selected_square
                to_row, to_col = row, col
                notation = self.engine.make_move(from_row, from_col, to_row, to_col)
                self.last_move = ((from_row, from_col), (to_row, to_col))
                self._append_move_to_log(notation)

                self.selected_square = None
                self.legal_moves = []

                # redraw after human move
                self._draw_board()

                # if this is HvAI and now it's AI's turn, auto-call AI
                self._maybe_trigger_ai_after_human_move()
                return
            else:
                # maybe selecting another piece of the same side
                if piece and piece[0] == self.engine.side_to_move():
                    self.selected_square = (row, col)
                    self.legal_moves = self.engine.get_legal_moves_from(row, col)
                else:
                    self.selected_square = None
                    self.legal_moves = []

        # final redraw
        self._draw_board()

    def _append_move_to_log(self, notation):
        move_index = len(self.engine.move_history)
        self.move_log.insert("end", f"{move_index}. {notation}")
        self.move_log.see("end")

    def on_new_game(self):
        if self.config["mode"] == "classic":
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

        if self.engine.move_stack:
            fr, fc, tr, tc, piece, cap, prev = self.engine.move_stack[-1]
            self.last_move = ((fr, fc), (tr, tc))
        else:
            self.last_move = None

        self.selected_square = None
        self.legal_moves = []
        self._draw_board()

    def on_ai_move(self):
        gt = self.config["game_type"]

        # 1) No AI in Human vs Human
        if gt == "HvH":
            self.status_var.set("No AI here – this is Human vs Human.")
            return

        # 2) Decide which AI settings to use (algo + depth)
        ai_side = self.config.get("ai_side", "b")  # default AI side for HvAI = Black

        if gt == "HvAI":
            # Only move when it's AI's turn
            if (ai_side == "w" and self.engine.side_to_move() != "w") or (
                ai_side == "b" and self.engine.side_to_move() != "b"
            ):
                self.status_var.set("It's the human's turn, not AI.")
                return

            algo = self.config["ai1_algo"]
            depth = int(self.config.get("ai1_depth", 3))

        else:  # AIvAI
            # choose which AI config based on side to move
            if self.engine.side_to_move() == "w":
                algo = self.config["ai1_algo"]
                depth = int(self.config.get("ai1_depth", 3))
            else:
                algo = self.config["ai2_algo"]
                depth = int(self.config.get("ai2_depth", 3))

        # 3) Map UI algo names -> engine method strings
        name_map = {
            "Minimax": "minimax",
            "Alpha-Beta": "alphabeta",
            "MCTS": "mcts",
            "Random": "random",
        }
        engine_algo = name_map.get(algo, "alphabeta")

        # 4) Ask engine for best move
        try:
            # your ChessEngine.find_best_move(method=None, max_depth=3)
            move_coords = self.engine.find_best_move(engine_algo, depth)
        except TypeError:
            # fallback if engine ignores depth parameter
            move_coords = self.engine.find_best_move(engine_algo)

        if move_coords is None:
            self.status_var.set("No legal moves – game may be over.")
            return

        # 5) Handle different possible return formats
        #    (e.g. (r1, c1, r2, c2) or (r1, c1, r2, c2, extra...))
        seq = list(move_coords)
        if len(seq) < 4:
            self.status_var.set("Engine returned invalid move format.")
            return

        from_row, from_col, to_row, to_col = seq[:4]

        # 6) Apply move on our 2D board
        notation = self.engine.make_move(from_row, from_col, to_row, to_col)
        self.last_move = ((from_row, from_col), (to_row, to_col))
        self._append_move_to_log(notation)

        # 7) Refresh UI
        self._draw_board()
        self.status_var.set(
            f"AI ({algo}, depth {depth}) played • {self.engine.get_status()}"
        )


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


    def _maybe_trigger_ai_after_human_move(self):
        """If this is Human vs AI and it's now AI's turn, call on_ai_move automatically."""
        if self.config["game_type"] != "HvAI":
            return

        ai_side = self.config.get("ai_side", "b")  # default: AI = Black
        # After the human move, if side_to_move == ai_side, schedule AI move
        if self.engine.side_to_move() == ai_side:
            # small delay so UI can update first
            self.root.after(300, self.on_ai_move)

# --- RUN --------------------------------------------------------------------


if __name__ == "__main__":
    root = tk.Tk()
    app = ChessApp(root)
    root.mainloop()
