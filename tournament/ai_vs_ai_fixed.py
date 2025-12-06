import csv
import chess

from engine.chess_engine import ChessEngine

# If you prefer, you can import this dict from your existing ai_vs_ai.py
SEARCH_FUNCS = {
    "minimax":   lambda engine: engine.find_best_move("minimax"),
    "alphabeta": lambda engine: engine.find_best_move("alphabeta"),
    "iddfs":     lambda engine: engine.find_best_move("iddfs"),
    "mcts":      lambda engine: engine.find_best_move("mcts"),
    "random":    lambda engine: engine.find_best_move("random"),
}


# ----------------------------------------------------------------------
# Helper: load shared FENs from CSV
# ----------------------------------------------------------------------
def load_fens_from_csv(path):
    """
    Load FENs from a CSV created by generate_endgames.py.
    Assumes header: ID, FEN
    """
    fens = []
    with open(path, "r", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for row in reader:
            if not row:
                continue
            # row[1] is FEN if format is ID, FEN
            fens.append(row[1])
    return fens


# ----------------------------------------------------------------------
# Play a single game starting from a GIVEN FEN
# ----------------------------------------------------------------------
def play_single_game_fixed(white_algo, black_algo, start_fen, max_moves=100):
    """
    Plays one AI-vs-AI game starting from a FIXED FEN.

    Returns:
        result      (1 = white win, 0 = draw, -1 = black win)
        white_count
        black_count
        pieces      (final piece list)
        moves       (plies)
        used_fen    (starting FEN)
        draw_reason (None if decisive; otherwise move_limit / insufficient_material / stalemate / threefold / fifty_move / other)
    """
    engine = ChessEngine()
    engine.load_fen(start_fen)

    white_count, black_count = engine.count_pieces()
    pieces = engine.get_piece_list()
    move_counter = 0
    draw_reason = None

    # ------------- GAME LOOP -------------
    while not engine.is_game_over() and move_counter < max_moves:
        if engine.board.turn == chess.WHITE:
            SEARCH_FUNCS[white_algo](engine)
        else:
            SEARCH_FUNCS[black_algo](engine)

        move_counter += 1

    # ------------- RESULT LOGIC -------------
    # Checkmate
    if engine.board.is_checkmate():
        winner = "WHITE" if engine.board.turn == chess.BLACK else "BLACK"
        print(f"Checkmate! Winner: {winner}, moves: {move_counter}")
        return (
            1 if engine.board.turn == chess.BLACK else -1,
            white_count,
            black_count,
            pieces,
            move_counter,
            start_fen,
            None,  # draw_reason
        )

    # Move limit
    if move_counter >= max_moves and not engine.board.is_game_over():
        draw_reason = "move_limit"
        print(f"Draw by move limit ({max_moves} plies), moves: {move_counter}")
    else:
        # Other draw types
        if engine.board.is_stalemate():
            draw_reason = "stalemate"
            print(f"Draw by stalemate, moves: {move_counter}")
        elif engine.board.is_insufficient_material():
            draw_reason = "insufficient_material"
            print(f"Draw by insufficient material, moves: {move_counter}")
        elif engine.board.can_claim_fifty_moves():
            draw_reason = "fifty_move"
            print(f"Draw (50-move rule), moves: {move_counter}")
        elif engine.board.can_claim_threefold_repetition():
            draw_reason = "threefold"
            print(f"Draw (threefold repetition), moves: {move_counter}")
        else:
            draw_reason = "other"
            print(f"Draw (other reason), moves: {move_counter}")

    return (
        0,
        white_count,
        black_count,
        pieces,
        move_counter,
        start_fen,
        draw_reason,
    )


# ----------------------------------------------------------------------
# Run matchup on the SHARED FEN SET
# ----------------------------------------------------------------------
def run_matchup_fixed(
    white_algo,
    black_algo="random",
    games=50,
    log_file="results_fixed.csv",
    fen_file="endgame_positions.csv",
):
    """
    Runs many games between two agents, reusing a FIXED set of starting FENs.

    All matchups that use the same fen_file will play on the same positions
    (game 1 = FEN 1, game 2 = FEN 2, ... looping if games > num FENs).
    """
    print(f"Running {games} games on fixed positions: {white_algo} (white) vs {black_algo} (black)")
    fens = load_fens_from_csv(fen_file)
    if not fens:
        raise ValueError(f"No FENs loaded from {fen_file}")

    white_wins = 0
    black_wins = 0
    draws = 0
    total_moves = 0

    draw_counts = {
        "move_limit": 0,
        "insufficient_material": 0,
        "stalemate": 0,
        "threefold": 0,
        "fifty_move": 0,
        "other": 0,
        None: 0,  # for decisive games
    }

    with open(log_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Game",
            "WhiteAlgo",
            "BlackAlgo",
            "WhiteCount",
            "BlackCount",
            "Pieces",
            "Result",
            "Moves",
            "StartFEN",
            "DrawReason",
        ])

        for g in range(1, games + 1):
            start_fen = fens[(g - 1) % len(fens)]

            (
                result,
                white_count,
                black_count,
                pieces,
                moves,
                used_fen,
                draw_reason,
            ) = play_single_game_fixed(
                white_algo,
                black_algo,
                start_fen=start_fen,
                max_moves=100,
            )

            total_moves += moves

            if result == 1:
                white_wins += 1
            elif result == -1:
                black_wins += 1
            else:
                draws += 1

            draw_counts[draw_reason] = draw_counts.get(draw_reason, 0) + 1

            writer.writerow([
                g,
                white_algo,
                black_algo,
                white_count,
                black_count,
                pieces,
                result,
                moves,
                used_fen,
                draw_reason,
            ])

            print(
                f"Game {g}/{games}: result={result}, moves={moves}\n"
                f"  white_count={white_count}, black_count={black_count}\n"
                f"  start_fen={used_fen}\n"
                f"  draw_reason={draw_reason}\n"
            )

        # summary lines
        writer.writerow(["--- MATCH COMPLETE ---"])
        writer.writerow([f"{white_algo} (White) wins: {white_wins}"])
        writer.writerow([f"{black_algo} (Black) wins: {black_wins}"])
        writer.writerow([f"Draws: {draws}"])
        writer.writerow([f"Average game length: {total_moves / games:.1f} moves"])

        writer.writerow(["Draw breakdown:"])
        for reason in ["move_limit", "insufficient_material", "stalemate", "threefold", "fifty_move", "other"]:
            writer.writerow([reason, draw_counts.get(reason, 0)])

    print("\n--- MATCH COMPLETE (FIXED POSITIONS) ---")
    print(f"{white_algo} (White) wins: {white_wins}")
    print(f"{black_algo} (Black) wins: {black_wins}")
    print(f"Draws: {draws}")
    print(f"Average game length: {total_moves / games:.1f} moves")
    print("Draw breakdown:")
    for reason in ["move_limit", "insufficient_material", "stalemate", "threefold", "fifty_move", "other"]:
        print(f"  {reason}: {draw_counts.get(reason, 0)}")

    return {
        "white_wins": white_wins,
        "black_wins": black_wins,
        "draws": draws,
        "avg_moves": total_moves / games,
        "draw_counts": draw_counts,
    }

if __name__ == "__main__":
    run_matchup_fixed(
        "iddfs",# White
        "alphabeta",  # Black
        games=50,
        log_file="fixed_iddfs_ab.csv",
        fen_file="endgame_positions.csv",)