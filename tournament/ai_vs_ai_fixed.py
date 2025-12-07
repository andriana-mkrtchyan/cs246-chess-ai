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


import time
import csv

def compare_search_times(
    algo1: str,
    algo2: str,
    fen_file: str,
    samples: int = 50,
    log_file: str = "search_timing_log.csv"
):
    """
    Compare the average time per move of any two search algorithms.

    algo1, algo2: names of algorithms from SEARCH_FUNCS
    fen_file:     CSV containing starting FENs
    samples:      number of timing tests to run
    log_file:     CSV file where timing results will be saved
    """

    fens = load_fens_from_csv(fen_file)
    if not fens:
        raise ValueError(f"No FENs loaded from {fen_file}")

    total_time_1 = 0.0
    total_time_2 = 0.0
    calls_1 = 0
    calls_2 = 0

    # open CSV
    with open(log_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Index", "FEN", algo1 + "_time", algo2 + "_time"])

        for i in range(samples):
            fen = fens[i % len(fens)]

            # algo1 timing
            engine1 = ChessEngine()
            engine1.load_fen(fen)
            start = time.perf_counter()
            SEARCH_FUNCS[algo1](engine1)
            t1 = time.perf_counter() - start
            total_time_1 += t1
            calls_1 += 1

            # algo2 timing
            engine2 = ChessEngine()
            engine2.load_fen(fen)
            start = time.perf_counter()
            SEARCH_FUNCS[algo2](engine2)
            t2 = time.perf_counter() - start
            total_time_2 += t2
            calls_2 += 1

            # write row
            writer.writerow([i + 1, fen, f"{t1:.6f}", f"{t2:.6f}"])

    avg1 = total_time_1 / calls_1 if calls_1 else 0.0
    avg2 = total_time_2 / calls_2 if calls_2 else 0.0

    print("\n--- Search time comparison ---")
    print(f"Algorithms: {algo1} vs {algo2}")
    print(f"Samples: {samples}")
    print(f"{algo1}: total {total_time_1:.4f}s, avg {avg1:.6f}s per move")
    print(f"{algo2}: total {total_time_2:.4f}s, avg {avg2:.6f}s per move")
    print(f"Log saved to: {log_file}")

    return {
        "algo1": algo1,
        "algo2": algo2,
        "samples": samples,
        "algo1_total": total_time_1,
        "algo2_total": total_time_2,
        "algo1_avg": avg1,
        "algo2_avg": avg2,
        "log_file": log_file,
    }

import time
import csv


def compare_all_algorithms_search_time(
    algos,
    fen_file: str,
    samples: int = 50,
    log_file: str = "search_timing_all_algos.csv",
):
    """
    Search-time benchmark on fixed positions.

    For each FEN, calls each algorithm exactly once (one move search)
    and measures how long the search takes. Prints total and average
    time per move for each algorithm and saves raw timings to CSV.
    """
    # validate algorithms
    for a in algos:
        if a not in SEARCH_FUNCS:
            raise ValueError(f"Unknown algorithm: {a}")

    fens = load_fens_from_csv(fen_file)
    if not fens:
        raise ValueError(f"No FENs loaded from {fen_file}")

    total_time = {a: 0.0 for a in algos}
    calls = {a: 0 for a in algos}

    # CSV with per-position timings
    with open(log_file, "w", newline="") as f:
        writer = csv.writer(f)
        header = ["Index", "FEN"] + [f"{a}_time" for a in algos]
        writer.writerow(header)

        for i in range(samples):
            fen = fens[i % len(fens)]
            row_times = []

            for a in algos:
                engine = ChessEngine()
                engine.load_fen(fen)

                start = time.perf_counter()
                SEARCH_FUNCS[a](engine)   # full engine logic (like test 1)
                dt = time.perf_counter() - start

                total_time[a] += dt
                calls[a] += 1
                row_times.append(f"{dt:.6f}")

            writer.writerow([i + 1, fen] + row_times)

    # print summary in "test 1" style
    print("\n--- Search time comparison (all algorithms) ---")
    print(f"Samples per algorithm: {samples}")
    print(f"Log saved to: {log_file}")

    stats = {}
    for a in algos:
        avg = total_time[a] / calls[a] if calls[a] else 0.0
        stats[a] = {
            "total_time": total_time[a],
            "calls": calls[a],
            "avg_time_per_move": avg,
        }
        print(f"{a}: total {total_time[a]:.4f}s, avg {avg:.6f}s per move")

    return stats


if __name__ == "__main__":
    compare_all_algorithms_search_time(
        algos=["minimax", "alphabeta", "iddfs", "mcts", "random"],
        fen_file="endgame_positions.csv",
        samples=50,
        log_file="search_timing_all_algos01 .csv",
    )




<<<<<<< HEAD
# if __name__ == "__main__":
#     compare_search_times(
#         algo1="alphabeta",
#         algo2="mcts",
#         fen_file="endgame_positions.csv",
#         samples=30,
#         log_file="timing_alphabeta_vs_mcts.csv"
#     )



=======
if __name__ == "__main__":
    run_matchup_fixed(
        "iddfs",
        "alphabeta",
        games=50,
        log_file="fixed_iddfs_ab.csv",
        fen_file="endgame_positions.csv",
    )

# if __name__ == "__main__":
#     compare_search_times(
#         algo1="minimax",
#         algo2="random",
#         fen_file="endgame_positions.csv",
#         samples=50,
#         log_file="timing___minmaxdept5_vs_random.csv"
#     )
>>>>>>> 2b17c51 (new ui and working program)
