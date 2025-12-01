import random
import chess
from config.constants import PIECE_VALUES
from ai.search_algorithms import (
    minimax,
    alpha_beta,
    iterative_deepening,
    mcts,
)
from ai.evaluation import evaluate_position


# --- ENGINE USING python-chess ---------------------------------------------


class ChessEngine:
    """
    Engine wrapper around python-chess.

    - Uses chess.Board for full rules (check, mate, stalemate, legal moves, promotion)
    - Exposes a simple 2D board (["wP", "bK", ...]) for the UI
    - Tracks move history & captured pieces
    - Supports undo
    - Has AI hook that can use minimax / alpha-beta / IDDFS / MCTS
    """

    def __init__(self):
        self.board = chess.Board()
        self.move_history = []      # SAN strings for display
        self.white_captures = []
        self.black_captures = []
        self._capture_history = []  # parallel stack for undo (stores "wP"/"bQ"/None)

    # --- position setup -----------------------------------------------------

    def reset_to_start_position(self):
        self.board = chess.Board()
        self.move_history.clear()
        self.white_captures.clear()
        self.black_captures.clear()
        self._capture_history.clear()

    def reset_to_endgame_position(self):
        """
        ENDGAME MODE SETUP.
        Generate a random low-material legal endgame position.
        """
        fen = ChessEngine.random_endgame_fen()
        self.board = chess.Board(fen)

        self.move_history.clear()
        self.white_captures.clear()
        self.black_captures.clear()
        self._capture_history.clear()

    def load_fen(self, fen: str):
        """
        Replace the current board with the position given by FEN.
        Clears histories (for testing / endgame experiments).
        """
        self.board = chess.Board(fen)
        self.move_history.clear()
        self.white_captures.clear()
        self.black_captures.clear()
        self._capture_history.clear()

    @staticmethod
    def random_endgame_fen(min_pieces=3, max_pieces=6):
        """
        Generate a random legal, NON-GAME-OVER endgame FEN.

        - always includes both kings
        - total number of pieces is between min_pieces and max_pieces
        - side to move is random
        """
        while True:
            board = chess.Board(None)

            # all squares, shuffled
            squares = list(chess.SQUARES)
            random.shuffle(squares)

            # place kings first
            wk = squares.pop()
            bk = squares.pop()
            board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
            board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))

            # how many extra pieces to add (beyond the 2 kings)
            num_extra = random.randint(max(0, min_pieces - 2), max_pieces - 2)

            piece_types = [chess.PAWN, chess.KNIGHT, chess.BISHOP,
                           chess.ROOK, chess.QUEEN]
            colors = [chess.WHITE, chess.BLACK]

            for _ in range(num_extra):
                if not squares:
                    break
                sq = squares.pop()
                ptype = random.choice(piece_types)
                color = random.choice(colors)

                # forbid pawns on 1st/8th rank to avoid illegal or weird promo states
                if ptype == chess.PAWN and (sq < 8 or sq >= 56):
                    continue

                board.set_piece_at(sq, chess.Piece(ptype, color))

            # random side to move
            board.turn = random.choice([chess.WHITE, chess.BLACK])

            # make sure the position is legal
            if not board.is_valid():
                continue

            # skip positions where the game is already finished
            if board.is_game_over():
                continue

            return board.fen()

    # --- helpers ------------------------------------------------------------

    def side_to_move(self):
        return "w" if self.board.turn == chess.WHITE else "b"

    def _square_to_rc(self, sq: chess.Square):
        """
        python-chess:
            file = 0..7  -> a..h
            rank = 0..7  -> 1..8
        UI:
            row 0 at top (rank 8), row 7 bottom (rank 1)
        """
        file = chess.square_file(sq)
        rank = chess.square_rank(sq)
        row = 7 - rank
        col = file
        return row, col

    def _rc_to_square(self, row: int, col: int) -> chess.Square:
        file = col
        rank = 7 - row
        return chess.square(file, rank)

    def get_board(self):
        """
        Return 8x8 board with strings like "wP", "bK" or "" for empty.
        """
        grid = [[""] * 8 for _ in range(8)]
        for sq, piece in self.board.piece_map().items():
            row, col = self._square_to_rc(sq)
            color = "w" if piece.color == chess.WHITE else "b"
            ptype = piece.symbol().upper()
            grid[row][col] = color + ptype
        return grid

    # --- move generation & making moves ------------------------------------

    def get_legal_moves_from(self, row, col):
        """
        Return list of (r, c) for legal moves from this square.
        """
        sq_from = self._rc_to_square(row, col)
        piece = self.board.piece_at(sq_from)
        if piece is None:
            return []
        if (piece.color == chess.WHITE and self.side_to_move() != "w") or \
           (piece.color == chess.BLACK and self.side_to_move() != "b"):
            return []

        moves = []
        for mv in self.board.legal_moves:
            if mv.from_square == sq_from:
                r, c = self._square_to_rc(mv.to_square)
                moves.append((r, c))
        return moves

    def make_move(self, from_row, from_col, to_row, to_col):
        """
        Execute a move if legal; return notation string or None if illegal.
        Handles automatic promotion to queen.
        """
        sq_from = self._rc_to_square(from_row, from_col)
        sq_to = self._rc_to_square(to_row, to_col)
        piece = self.board.piece_at(sq_from)
        if piece is None:
            return None

        # Determine promotion (always promote to queen for simplicity)
        promotion = None
        if piece.piece_type == chess.PAWN:
            rank_to = chess.square_rank(sq_to)
            if (piece.color == chess.WHITE and rank_to == 7) or \
               (piece.color == chess.BLACK and rank_to == 0):
                promotion = chess.QUEEN

        move = chess.Move(sq_from, sq_to, promotion=promotion)
        if move not in self.board.legal_moves:
            return None

        # capture info BEFORE pushing
        captured_piece = self.board.piece_at(sq_to)
        captured_str = None
        if captured_piece:
            c_color = "w" if captured_piece.color == chess.WHITE else "b"
            c_ptype = captured_piece.symbol().upper()
            captured_str = c_color + c_ptype

        # IMPORTANT: compute SAN BEFORE push
        san = self.board.san(move)

        # now push the move
        self.board.push(move)

        # update captures + capture history (for undo)
        self._capture_history.append(captured_str)
        if captured_str:
            if piece.color == chess.WHITE:
                self.white_captures.append(captured_str)
            else:
                self.black_captures.append(captured_str)

        self.move_history.append(san)
        return san

    def undo_last_move(self):
        """
        Undo last move; return notation undone or None.
        """
        if not self.board.move_stack:
            return None

        # pop from python-chess
        self.board.pop()

        # pop our histories
        undone = self.move_history.pop() if self.move_history else None
        captured_str = self._capture_history.pop() if self._capture_history else None

        if captured_str:
            if captured_str in self.white_captures:
                self.white_captures.remove(captured_str)
            elif captured_str in self.black_captures:
                self.black_captures.remove(captured_str)

        return undone

    # --- game status & evaluation ------------------------------------------

    def get_status(self):
        # checkmate
        if self.board.is_checkmate():
            # side to move is checkmated, so the other side wins
            winner = "Black" if self.board.turn == chess.WHITE else "White"
            return f"Checkmate • {winner} wins"

        # stalemate
        if self.board.is_stalemate():
            return "Stalemate • Draw"

        # insufficient material (no side can force mate)
        if self.board.is_insufficient_material():
            return "Draw • Insufficient material"

        # in-check info
        if self.board.is_check():
            return ("White to move (in check)"
                    if self.board.turn == chess.WHITE
                    else "Black to move (in check)")

        # normal
        return "White to move" if self.board.turn == chess.WHITE else "Black to move"

    def is_game_over(self):
        return self.board.is_game_over()

    def get_captures(self):
        return self.white_captures, self.black_captures

    def get_material_balance(self):
        """
        Pure material difference (for UI display).
        """
        score = 0
        for sq, piece in self.board.piece_map().items():
            val = PIECE_VALUES.get(piece.symbol().upper(), 0)
            score += val if piece.color == chess.WHITE else -val
        return score

    def get_static_evaluation(self):
        """
        Full heuristic evaluation using ai.evaluation.evaluate_position.
        Positive = good for White, negative = good for Black.
        """
        return evaluate_position(self.board)

    def has_mating_material(self, side: str) -> bool:
        """
        Return True if the given side ('w' or 'b') has enough material
        to *possibly* deliver checkmate.

        We use a standard simple rule:
        - any pawn, rook or queen  -> enough material
        - bishop+bishop or bishop+knight -> enough
        - otherwise (lone king, king+single bishop, king+single knight) -> no
        """
        color = chess.WHITE if side == "w" else chess.BLACK
        pieces = [p for p in self.board.piece_map().values() if p.color == color]

        pawns = sum(1 for p in pieces if p.piece_type == chess.PAWN)
        rooks = sum(1 for p in pieces if p.piece_type == chess.ROOK)
        queens = sum(1 for p in pieces if p.piece_type == chess.QUEEN)
        bishops = sum(1 for p in pieces if p.piece_type == chess.BISHOP)
        knights = sum(1 for p in pieces if p.piece_type == chess.KNIGHT)

        # any "big" material or pawn is clearly enough
        if pawns > 0 or rooks > 0 or queens > 0:
            return True

        # two bishops, or bishop+knight can in practice deliver mate
        if bishops >= 2:
            return True
        if bishops >= 1 and knights >= 1:
            return True

        # otherwise we treat it as insufficient (K, KB, KN…)
        return False

    # --- AI hook ------------------------------------------------------------

    def find_best_move(self, method: str = "alphabeta"):
        """
        Use AI search to find and execute the best move.

        method:
            - "minimax"   -> pure minimax
            - "alphabeta" -> minimax with alpha-beta + quiescence
            - "iddfs"     -> iterative deepening over alpha-beta
            - "mcts"      -> Monte Carlo Tree Search
            - anything else -> random legal move
        Returns (from_row, from_col, to_row, to_col, notation) or None.
        """
        if self.is_game_over():
            return None

        legal = list(self.board.legal_moves)
        if not legal:
            return None

        method = (method or "alphabeta").lower()
        maximizing = (self.board.turn == chess.WHITE)

        # choose search algorithm
        if method == "minimax":
            _, best_move = minimax(self.board, depth=3, maximizing=maximizing)
        elif method == "iddfs":
            best_move = iterative_deepening(
                self.board,
                max_depth=5,
            )
        elif method == "mcts":
            best_move = mcts(
                self.board,
                simulations=300,
            )
        elif method=="alphabeta":
            _, best_move = alpha_beta(
                self.board,
                depth=4,
                alpha=-float("inf"),
                beta=float("inf"),
                maximizing=maximizing,
            )
        else:
            best_move = random.choice(legal)

        if best_move is None:
            return None

        # ----------------------
        #  HANDLE PROMOTION SAFELY
        # ----------------------
        from_sq = best_move.from_square
        to_sq = best_move.to_square
        moving_piece = self.board.piece_at(from_sq)

        promotion_piece_type = None
        if moving_piece and moving_piece.piece_type == chess.PAWN:
            target_rank = chess.square_rank(to_sq)
            if (moving_piece.color == chess.WHITE and target_rank == 7) or \
                    (moving_piece.color == chess.BLACK and target_rank == 0):
                promotion_piece_type = chess.QUEEN

        # convert to row/col and actually make the move using existing logic
        from_row, from_col = self._square_to_rc(from_sq)
        to_row, to_col = self._square_to_rc(to_sq)
        san = self.make_move(
            from_row,
            from_col,
            to_row,
            to_col)
        # If the search move was missing a promotion flag,
        # we retry with a QUEEN promotion.
        if san is None and promotion_piece_type is not None:
            move = chess.Move(from_sq, to_sq, promotion=promotion_piece_type)
            if move in self.board.legal_moves:
                self.board.push(move)
                san = self.board.san(move)

        if san is None:
            return None

        return from_row, from_col, to_row, to_col, san

    # --- logging ------------------------------------------------------------

    def count_pieces(self):
        white = sum(1 for p in self.board.piece_map().values() if p.color == chess.WHITE)
        black = sum(1 for p in self.board.piece_map().values() if p.color == chess.BLACK)
        return white, black

    def get_piece_list(self):
        """
        Return a list of tuples: (color, piece_type, square_name)
        """
        pieces = []
        for sq, piece in self.board.piece_map().items():
            color = 'w' if piece.color == chess.WHITE else 'b'
            ptype = piece.symbol().upper()
            square_name = chess.square_name(sq)
            pieces.append((color, ptype, square_name))
        return pieces
