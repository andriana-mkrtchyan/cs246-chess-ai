import csv
import chess

from engine.chess_engine import ChessEngine

SEARCH_FUNCS = {
    "minimax": lambda engine: engine.find_best_move("minimax"),
    "alphabeta": lambda engine: engine.find_best_move("alphabeta"),
    "iddfs": lambda engine: engine.find_best_move("iddfs"),
    "mcts": lambda engine: engine.find_best_move("mcts"),
    "random": lambda engine: engine.find_best_move("random"),
}


def play_single_game(white_algo: str, black_algo: str, max_moves: int = 100):
    """
    Play a single AI-vs-AI game and return:
    (result, white_count, black_count, pieces, moves, draw_reason).

    result: 1 (white win), 0 (draw), -1 (black win)
    draw_reason: one of None, 'move_limit', 'insufficient_material',
                 'stalemate', 'threefold', 'fifty_move', 'other'
    """
    engine = ChessEngine()
    engine.reset_to_endgame_position()

    white_count, black_count = engine.count_pieces()
    pieces = engine.get_piece_list()
    move_counter = 0

    while not engine.is_game_over() and move_counter < max_moves:
        if engine.board.turn == chess.WHITE:
            SEARCH_FUNCS[white_algo](engine)
        else:
            SEARCH_FUNCS[black_algo](engine)
        move_counter += 1

    # Checkmate: decisive game
    if engine.board.is_checkmate():
        winner = "WHITE" if engine.board.turn == chess.BLACK else "BLACK"
        print(f"Checkmate! Winner: {winner}, moves: {move_counter}")
        result = 1 if engine.board.turn == chess.BLACK else -1
        return result, white_count, black_count, pieces, move_counter, None

    # Draw by move limit (custom rule)
    if move_counter >= max_moves and not engine.board.is_game_over():
        print(f"Draw by move limit ({max_moves} plies), moves: {move_counter}")
        return 0, white_count, black_count, pieces, move_counter, "move_limit"

    # Draw by standard rules
    if engine.board.is_stalemate():
        print(f"Draw by stalemate, moves: {move_counter}")
        draw_reason = "stalemate"
    elif engine.board.is_insufficient_material():
        print(f"Draw by insufficient material, moves: {move_counter}")
        draw_reason = "insufficient_material"
    elif engine.board.can_claim_fifty_moves():
        print(f"Draw (fifty-move rule claim possible), moves: {move_counter}")
        draw_reason = "fifty_move"
    elif engine.board.can_claim_threefold_repetition():
        print(f"Draw (threefold repetition), moves: {move_counter}")
        draw_reason = "threefold"
    else:
        print(f"Draw (other reason), moves: {move_counter}")
        draw_reason = "other"

    return 0, white_count, black_count, pieces, move_counter, draw_reason


def run_matchup(white_algo: str, black_algo: str = "random", games: int = 100, log_file: str = "results.csv"):
    """
    Run multiple games between two algorithms and write results to a CSV file.

    Returns a summary dictionary with win/draw counts, average moves,
    and draw reason counts.
    """
    print(f"Running {games} games: {white_algo} (white) vs {black_algo} (black)")

    white_wins = 0
    black_wins = 0
    draws = 0
    total_moves = 0

    draw_move_limit = 0
    draw_insufficient = 0
    draw_stalemate = 0
    draw_threefold = 0
    draw_fifty = 0
    draw_other = 0

    with open(log_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Game",
            "WhiteAlgo",
            "BlackAlgo",
            "White count",
            "Black count",
            "Pieces",
            "Result",
            "Moves",
            "DrawReason",
        ])

        for g in range(1, games + 1):
            (
                result,
                white_count,
                black_count,
                pieces,
                moves,
                draw_reason,
            ) = play_single_game(white_algo, black_algo)

            total_moves += moves

            if result == 1:
                white_wins += 1
            elif result == -1:
                black_wins += 1
            else:
                draws += 1
                if draw_reason == "move_limit":
                    draw_move_limit += 1
                elif draw_reason == "insufficient_material":
                    draw_insufficient += 1
                elif draw_reason == "stalemate":
                    draw_stalemate += 1
                elif draw_reason == "threefold":
                    draw_threefold += 1
                elif draw_reason == "fifty_move":
                    draw_fifty += 1
                else:
                    draw_other += 1

            writer.writerow([
                g,
                white_algo,
                black_algo,
                white_count,
                black_count,
                pieces,
                result,
                moves,
                draw_reason if draw_reason is not None else "",
            ])

            print(
                f"Game {g}/{games}: result={result}  moves={moves} "
                f"\nwhite count={white_count} black count={black_count} "
                f"\npieces = {pieces}\n "
            )

        writer.writerow(["\n--- MATCH COMPLETE ---"])
        writer.writerow([f"{white_algo} (White) wins: {white_wins}"])
        writer.writerow([f"{black_algo} (Black) wins: {black_wins}"])
        writer.writerow([f"Draws: {draws}"])
        writer.writerow([f"Average game length: {total_moves / games:.1f} moves"])
        writer.writerow(["Draw breakdown:"])
        writer.writerow([f"move_limit: {draw_move_limit}"])
        writer.writerow([f"insufficient_material: {draw_insufficient}"])
        writer.writerow([f"stalemate: {draw_stalemate}"])
        writer.writerow([f"threefold: {draw_threefold}"])
        writer.writerow([f"fifty_move: {draw_fifty}"])
        writer.writerow([f"other: {draw_other}"])

    print("\n--- MATCH COMPLETE ---")
    print(f"{white_algo} (White) wins: {white_wins}")
    print(f"{black_algo} (Black) wins: {black_wins}")
    print(f"Draws: {draws}")
    print(f"Average game length: {total_moves / games:.1f} moves")

    print("Draw breakdown:")
    print(f"  Move limit:           {draw_move_limit}")
    print(f"  Insufficient material:{draw_insufficient}")
    print(f"  Stalemate:            {draw_stalemate}")
    print(f"  Threefold repetition: {draw_threefold}")
    print(f"  Fifty-move rule:      {draw_fifty}")
    print(f"  Other:                {draw_other}")

    return {
        "white_wins": white_wins,
        "black_wins": black_wins,
        "draws": draws,
        "avg_moves": total_moves / games,
        "draws_move_limit": draw_move_limit,
        "draws_insufficient": draw_insufficient,
        "draws_stalemate": draw_stalemate,
        "draws_threefold": draw_threefold,
        "draws_fifty": draw_fifty,
        "draws_other": draw_other,
    }


if __name__ == "__main__":
    run_matchup("iddfs", "mcts", games=50, log_file="iddfs_4_mcts_300_50.csv")
