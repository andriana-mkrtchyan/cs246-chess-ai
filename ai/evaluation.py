import chess
from config.constants import PIECE_VALUES


# ======================================================================
# PHASE DETECTION (opening, middlegame, endgame)
# Based on total material left on the board
# ======================================================================

def game_phase(board: chess.Board):
    """Return 'opening', 'middlegame', or 'endgame'."""
    total_major = 0
    for piece in board.piece_map().values():
        if piece.piece_type in (chess.QUEEN, chess.ROOK):
            total_major += 1

    if total_major >= 6:
        return "opening"
    elif total_major >= 3:
        return "middlegame"
    return "endgame"


# ======================================================================
# MOBILITY
# ======================================================================

def mobility(board: chess.Board, color: chess.Color):
    """Mobility = number of legal moves for each side."""
    return sum(1 for move in board.legal_moves if board.piece_at(move.from_square).color == color)


# ======================================================================
# PAWN STRUCTURE
# doubled, isolated, passed pawns
# ======================================================================

def pawn_structure(board: chess.Board, color: chess.Color):
    score = 0
    pawns = board.pieces(chess.PAWN, color)

    files = [chess.square_file(sq) for sq in pawns]

    # doubled pawns = bad
    for f in set(files):
        count = files.count(f)
        if count > 1:
            score -= 0.2 * (count - 1)

    # isolated pawns
    for sq in pawns:
        file = chess.square_file(sq)
        neighbors = {file - 1, file + 1}
        isolated = True
        for other in pawns:
            if chess.square_file(other) in neighbors:
                isolated = False
        if isolated:
            score -= 0.3

    # passed pawns
    for sq in pawns:
        rank = chess.square_rank(sq)
        is_passed = True
        for other in board.pieces(chess.PAWN, not color):
            if chess.square_file(other) == chess.square_file(sq):
                if (color == chess.WHITE and chess.square_rank(other) > rank) or \
                   (color == chess.BLACK and chess.square_rank(other) < rank):
                    is_passed = False
        if is_passed:
            score += 0.5

    return score


# ======================================================================
# KING SAFETY (very simplified)
# ======================================================================

def king_safety(board: chess.Board, color: chess.Color):
    king = board.king(color)
    if king is None:
        return 0

    rank = chess.square_rank(king)

    # King safety by game phase
    phase = game_phase(board)
    if phase == "opening":
        # encourage castling / keeping king on back rank
        if rank != (0 if color == chess.WHITE else 7):
            return -0.5
    elif phase == "endgame":
        # centralized king is good in endgame
        return (3 - abs(3.5 - chess.square_file(king))) * 0.1

    return 0


# ======================================================================
# PIECE-SQUARE TABLES (PST for Knight moves)
# ======================================================================

KNIGHT_TABLE = [
    -0.5, -0.4, -0.3, -0.3, -0.3, -0.3, -0.4, -0.5,
    -0.4, -0.2,  0.0,  0.0,  0.0,  0.0, -0.2, -0.4,
    -0.3,  0.0,  0.1,  0.15, 0.15, 0.1,  0.0, -0.3,
    -0.3,  0.0,  0.15, 0.20, 0.20, 0.15, 0.0, -0.3,
    -0.3,  0.0,  0.15, 0.20, 0.20, 0.15, 0.0, -0.3,
    -0.3,  0.0,  0.1,  0.15, 0.15, 0.1,  0.0, -0.3,
    -0.4, -0.2,  0.0,  0.0,  0.0,  0.0, -0.2, -0.4,
    -0.5, -0.4, -0.3, -0.3, -0.3, -0.3, -0.4, -0.5,
]


def pst_bonus(piece, square):
    if piece.piece_type == chess.KNIGHT:
        return KNIGHT_TABLE[square]
    return 0


# ======================================================================
# MAIN EVALUATION FUNCTION — COMBINES ALL HEURISTICS
# ======================================================================

def evaluate_position(board: chess.Board):
    if board.is_checkmate():
        return 9999 if board.turn == chess.BLACK else -9999
    if board.is_stalemate():
        return 0

    score = 0

    # Material
    for sq, piece in board.piece_map().items():
        val = PIECE_VALUES[piece.symbol().upper()]
        if piece.color == chess.WHITE:
            score += val
        else:
            score -= val

        # PST bonus
        score += pst_bonus(piece, sq) * (1 if piece.color == chess.WHITE else -1)

    # Mobility
    score += 0.1 * (mobility(board, chess.WHITE) - mobility(board, chess.BLACK))

    # Pawn structure
    score += pawn_structure(board, chess.WHITE)
    score -= pawn_structure(board, chess.BLACK)

    # King safety
    score += king_safety(board, chess.WHITE)
    score -= king_safety(board, chess.BLACK)

    return score
