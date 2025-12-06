import chess
from config.constants import PIECE_VALUES


def game_phase(board: chess.Board):
    """Return the current game phase based on remaining major pieces."""
    total_major = sum(
        1 for p in board.piece_map().values()
        if p.piece_type in (chess.QUEEN, chess.ROOK)
    )
    if total_major >= 6:
        return "opening"
    elif total_major >= 3:
        return "middlegame"
    return "endgame"


def mobility(board: chess.Board, color: chess.Color):
    """
    Return the number of legal moves available for the given side.
    Temporarily switches board.turn to generate legal moves for that color.
    """
    original_turn = board.turn
    board.turn = color
    count = sum(1 for _ in board.legal_moves)
    board.turn = original_turn
    return count


def pawn_structure(board: chess.Board, color: chess.Color):
    """Return a pawn structure score including doubled, isolated, and passed pawns."""
    score = 0
    pawns = board.pieces(chess.PAWN, color)
    files = [chess.square_file(sq) for sq in pawns]

    # Doubled pawns
    for f in set(files):
        count = files.count(f)
        if count > 1:
            score -= 0.2 * (count - 1)

    # Isolated pawns
    for sq in pawns:
        file = chess.square_file(sq)
        neighbors = {file - 1, file + 1}
        isolated = True
        for other in pawns:
            if chess.square_file(other) in neighbors:
                isolated = False
        if isolated:
            score -= 0.3

    # Passed pawns
    for sq in pawns:
        file = chess.square_file(sq)
        rank = chess.square_rank(sq)
        is_passed = True

        for other in board.pieces(chess.PAWN, not color):
            other_file = chess.square_file(other)
            other_rank = chess.square_rank(other)

            # Enemy pawn ahead of this pawn in the same or adjacent file
            if abs(other_file - file) <= 1:
                if (color == chess.WHITE and other_rank > rank) or \
                   (color == chess.BLACK and other_rank < rank):
                    is_passed = False
                    break

        if is_passed:
            score += 0.5

    return score


def king_safety(board: chess.Board, color: chess.Color):
    """Return a king safety score based on game phase and king positioning."""
    king = board.king(color)
    if king is None:
        return 0

    rank = chess.square_rank(king)
    file = chess.square_file(king)
    phase = game_phase(board)

    if phase in ("opening", "middlegame"):
        # Prefer a king on the back rank
        if rank != (0 if color == chess.WHITE else 7):
            return -0.5
        # Small bonus for typical castling files
        if file in (1, 6):
            return 0.2
        return 0

    # Endgame: centralized king is beneficial
    center_distance = abs(file - 3.5) + abs(rank - 3.5)
    return -(center_distance * 0.3)


def king_opposition(board: chess.Board):
    """
    Return a bonus based on king-to-king proximity in endgames.
    Applies only in simplified endgame positions.
    """
    if game_phase(board) != "endgame":
        return 0

    wk = board.king(chess.WHITE)
    bk = board.king(chess.BLACK)
    if wk is None or bk is None:
        return 0

    wr, wc = chess.square_rank(wk), chess.square_file(wk)
    br, bc = chess.square_rank(bk), chess.square_file(bk)
    dist = abs(wr - br) + abs(wc - bc)

    return (6 - dist) * 0.2  # White positive, Black negative applied later


def endgame_pressure(board: chess.Board):
    """Return a score encouraging edge pressure in rook/queen endgames."""
    if game_phase(board) != "endgame":
        return 0

    score = 0

    for color in (chess.WHITE, chess.BLACK):
        king_sq = board.king(not color)
        if king_sq is None:
            continue

        enemy_rank = chess.square_rank(king_sq)
        enemy_file = chess.square_file(king_sq)
        dist_edge = min(enemy_rank, 7 - enemy_rank, enemy_file, 7 - enemy_file)

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


def evaluate_position(board: chess.Board):
    """Return a full evaluation score combining material and positional heuristics."""

    # Checkmate
    if board.is_checkmate():
        return 9999 if board.turn == chess.BLACK else -9999

    # Draws: penalize drawing when clearly winning (stalemate, threefold, 50-move)
    if board.is_stalemate() or board.can_claim_threefold_repetition() or board.can_claim_fifty_moves():
        material = 0
        for piece in board.piece_map().values():
            mat_val = PIECE_VALUES[piece.symbol().upper()]
            material += mat_val if piece.color == chess.WHITE else -mat_val

        # If one side is clearly ahead, treat draw as bad for that side
        if abs(material) >= 3:
            return -material * 2
        return 0

    score = 0

    # Material
    for piece in board.piece_map().values():
        val = PIECE_VALUES[piece.symbol().upper()]
        if piece.color == chess.WHITE:
            score += val
        else:
            score -= val

    # Mobility
    score += 0.1 * (mobility(board, chess.WHITE) - mobility(board, chess.BLACK))

    # Pawn structure
    score += pawn_structure(board, chess.WHITE)
    score -= pawn_structure(board, chess.BLACK)

    # King safety
    score += king_safety(board, chess.WHITE)
    score -= king_safety(board, chess.BLACK)

    # King opposition and endgame pressure
    score += king_opposition(board)
    score += endgame_pressure(board)

    # Extra endgame king activity and king distance
    if game_phase(board) == "endgame":
        wk = board.king(chess.WHITE)
        bk = board.king(chess.BLACK)
        if wk is not None and bk is not None:
            wr, wc = chess.square_rank(wk), chess.square_file(wk)
            br, bc = chess.square_rank(bk), chess.square_file(bk)

            # Stronger king centralization
            score += (3.5 - abs(wr - 3.5)) * 1.2
            score -= (3.5 - abs(br - 3.5)) * 1.2

            # Encourage kings getting closer (helps mating nets)
            king_dist = abs(wr - br) + abs(wc - bc)
            score -= king_dist * 0.8

    # Small bonus for giving check (tactical pressure)
    if board.is_check():
        score += 0.8 if board.turn == chess.BLACK else -0.8

    return score
