import csv
import chess
import time

from engine.chess_engine import ChessEngine

SEARCH_FUNCS = {
    "minimax":   lambda engine: engine.find_best_move("minimax"),
    "alphabeta": lambda engine: engine.find_best_move("alphabeta"),
    "iddfs":     lambda engine: engine.find_best_move("iddfs"),
    "mcts":      lambda engine: engine.find_best_move("mcts"),
    "random":    lambda engine: engine.find_best_move("random"),
}


def load_fens_from_csv(path: str):
    """
    Load FEN strings from a CSV file with header [ID, FEN].

    Returns a list of FEN strings.
    """
    fens = []
    with open(path, "r", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for row in reader:
            if not row:
                continue
            fens.append(row[1])
    return fens


def play_single_game_fixed(white_algo: str, black_algo: str, start_fen: str, max_moves: int = 100):
    """
    Play one AI-vs-AI game from a fixed starting FEN.

    Returns:
        result      (1 = white win, 0 = draw, -1 = black win)
        white_count
        black_count
        pieces      (final piece list)
        moves       (plies)
        used_fen    (starting FEN)
        draw_reason (None if decisive; otherwise a draw label)
    """
    engine = ChessEngine()
    engine.load_fen(start_fen)

    white_count, black_count = engine.count_pieces()
    pieces = engine.get_piece_list()
    move_counter = 0
    draw_reason = None

    while not engine.is_game_over() and move_counter < max_moves:
        if engine.board.turn == chess.WHITE:
            SEARCH_FUNCS[white_algo](engine)
        else:
            SEARCH_FUNCS[black_algo](engine)
        move_counter += 1

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
            None,
        )

    if move_counter >= max_moves and not engine.board.is_game_over():
        draw_reason = "move_limit"
        print(f"Draw by move limit ({max_moves} plies), moves: {move_counter}")
    else:
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


def run_matchup_fixed(
    white_algo: str,
    black_algo: str = "random",
    games: int = 50,
    log_file: str = "results_fixed.csv",
    fen_file: str = "endgame_positions.csv",
):
    """
    Run multiple games on a fixed set of starting FEN positions.

    Games reuse FENs from fen_file in order, looping if games > number of FENs.
    Results are written to a CSV file and a summary dictionary is returned.
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
        None: 0,
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


#Quick timing benchmark for minimax vs alpha-beta on fixed FENs
def compare_minimax_vs_alphabeta(fen_file: str, samples: int = 50):
    """
    Compare average time per move of minimax vs alpha-beta on fixed positions.

    For each FEN, runs one move search with minimax and one with alpha-beta,
    then reports total and average time for each algorithm.
    """
    fens = load_fens_from_csv(fen_file)
    if not fens:
        raise ValueError(f"No FENs loaded from {fen_file}")

    total_minimax_time = 0.0
    total_alphabeta_time = 0.0
    minimax_calls = 0
    alphabeta_calls = 0

    for i in range(samples):
        fen = fens[i % len(fens)]

        # minimax timing
        engine_min = ChessEngine()
        engine_min.load_fen(fen)
        start = time.perf_counter()
        SEARCH_FUNCS["minimax"](engine_min)
        total_minimax_time += time.perf_counter() - start
        minimax_calls += 1

        # alpha-beta timing
        engine_ab = ChessEngine()
        engine_ab.load_fen(fen)
        start = time.perf_counter()
        SEARCH_FUNCS["alphabeta"](engine_ab)
        total_alphabeta_time += time.perf_counter() - start
        alphabeta_calls += 1

    avg_minimax = total_minimax_time / minimax_calls if minimax_calls else 0.0
    avg_alphabeta = total_alphabeta_time / alphabeta_calls if alphabeta_calls else 0.0

    print("\n--- Search time comparison on fixed positions ---")
    print(f"Samples: {samples}")
    print(f"Minimax:   total {total_minimax_time:.4f}s, avg {avg_minimax:.6f}s per move")
    print(f"AlphaBeta: total {total_alphabeta_time:.4f}s, avg {avg_alphabeta:.6f}s per move")

    return {
        "samples": samples,
        "minimax_total": total_minimax_time,
        "alphabeta_total": total_alphabeta_time,
        "minimax_avg": avg_minimax,
        "alphabeta_avg": avg_alphabeta,
    }


# if __name__ == "__main__":
#     run_matchup_fixed(
#         "iddfs",
#         "alphabeta",
#         games=50,
#         log_file="fixed_iddfs_ab.csv",
#         fen_file="endgame_positions.csv",
#     )

if __name__ == "__main__":
    compare_minimax_vs_alphabeta(
        fen_file="endgame_positions.csv",
        samples=50
    )
