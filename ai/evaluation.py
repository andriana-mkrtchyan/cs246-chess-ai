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
    """
    Mobility = number of legal moves for the given side.
    python-chess only generates moves for board.turn,
    so we temporarily switch board.turn.
    """
    original_turn = board.turn
    board.turn = color
    count = sum(1 for _ in board.legal_moves)
    board.turn = original_turn
    return count

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

    # passed pawns (checks adjacent files too)
    for sq in pawns:
        file = chess.square_file(sq)
        rank = chess.square_rank(sq)
        is_passed = True

        for other in board.pieces(chess.PAWN, not color):
            other_file = chess.square_file(other)
            other_rank = chess.square_rank(other)

            # enemy pawn in same or adjacent file AND ahead of this pawn
            if abs(other_file - file) <= 1:
                if (color == chess.WHITE and other_rank > rank) or \
                        (color == chess.BLACK and other_rank < rank):
                    is_passed = False
                    break

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
    file = chess.square_file(king)
    # King safety by game phase
    phase = game_phase(board)
    if phase in ("opening", "middlegame"):
        # encourage castling / keeping king on back rank
        if rank != (0 if color == chess.WHITE else 7):
            return -0.5
        if file in (1, 6):
            return +0.2
        return 0
    else:
        center_distance = abs(file - 3.5) + abs(rank - 3.5)
        # centralized king is good in endgame
        return -(center_distance * 0.3)


# ======================================================================
# KING OPPOSITION / DISTANCE (ENDGAME)
# ======================================================================

def king_opposition(board: chess.Board):
    """
    Small bonus for taking opposition in K vs K type endings.
    Only applies if queens & rooks are mostly gone.
    """
    phase = game_phase(board)
    if phase != "endgame":
        return 0

    wk = board.king(chess.WHITE)
    bk = board.king(chess.BLACK)
    if wk is None or bk is None:
        return 0

    wr, wc = chess.square_rank(wk), chess.square_file(wk)
    br, bc = chess.square_rank(bk), chess.square_file(bk)

    # Manhattan distance
    dist = abs(wr - br) + abs(wc - bc)

    # Closer king is usually better
    return (6 - dist) * 0.2  # White gets +, Black gets - later


# ======================================================================
# SIMPLE ROOK/QUEEN ENDGAME PRESSURE
# ======================================================================

def endgame_pressure(board: chess.Board):
    """
    Bonus for pushing the enemy king toward the edge,
    common pattern in KQ vs K or KR vs K mates.
    """
    phase = game_phase(board)
    if phase != "endgame":
        return 0

    score = 0

    for color in (chess.WHITE, chess.BLACK):
        king_sq = board.king(not color)  # enemy king
        if king_sq is None:
            continue

        enemy_rank = chess.square_rank(king_sq)
        enemy_file = chess.square_file(king_sq)

        # distance from edge (edges = good target)
        dist_edge = min(enemy_rank, 7 - enemy_rank, enemy_file, 7 - enemy_file)

        # if attacker has heavy pieces, encourage cornering
        has_heavy = (
            len(board.pieces(chess.QUEEN, color)) > 0 or
            len(board.pieces(chess.ROOK, color)) > 0
        )

        if has_heavy:
            if color == chess.WHITE:
                score += (3 - dist_edge) * 0.4
            else:
                score -= (3 - dist_edge) * 0.4

    return score



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
        #score += pst_bonus(piece, sq) * (1 if piece.color == chess.WHITE else -1)

    # Mobility
    score += 0.1 * (mobility(board, chess.WHITE) - mobility(board, chess.BLACK))

    # Pawn structure
    score += pawn_structure(board, chess.WHITE)
    score -= pawn_structure(board, chess.BLACK)

    # King safety
    score += king_safety(board, chess.WHITE)
    score -= king_safety(board, chess.BLACK)

    # King opposition
    score += king_opposition(board)

    # Endgame pressure
    score += endgame_pressure(board)

    return score
