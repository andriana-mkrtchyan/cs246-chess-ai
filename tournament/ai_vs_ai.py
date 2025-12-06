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


def play_single_game(white_algo: str, black_algo: str, max_moves=100):
    """
    Play a single AI-vs-AI game and return:
    (result, white_piece_count, black_piece_count, piece_list, moves_played).

    result: 1 for White win, 0 for draw, -1 for Black win.
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

    if engine.board.is_checkmate():
        winner = "WHITE" if engine.board.turn == chess.BLACK else "BLACK"
        print(f"Move count: {move_counter}, Winner: {winner}")
        return (1 if engine.board.turn == chess.BLACK else -1), white_count, black_count, pieces, move_counter

    print("Draw, moves:", move_counter)
    return 0, white_count, black_count, pieces, move_counter


def run_matchup(white_algo, black_algo="random", games=100, log_file="results.csv"):
    """
    Run multiple AI-vs-AI games between two algorithms and log results to CSV.

    Returns a summary dictionary with white wins, black wins, draws,
    and average game length in moves.
    """
    print(f"Running {games} games: {white_algo} (white) vs {black_algo} (black)")

    white_wins = 0
    black_wins = 0
    draws = 0
    total_moves = 0

    with open(log_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Game", "WhiteAlgo", "BlackAlgo", "White count", "Black count", "Pieces", "Result", "Moves"])

        for g in range(1, games + 1):
            result, white_count, black_count, pieces, moves = play_single_game(white_algo, black_algo)
            total_moves += moves

            if result == 1:
                white_wins += 1
            elif result == -1:
                black_wins += 1
            else:
                draws += 1

            writer.writerow([g, white_algo, black_algo, white_count, black_count, pieces, result, moves])
            print(
                f"Game {g}/{games}: result={result}  moves={moves} \n"
                f"white count={white_count} black count={black_count} \n"
                f"pieces = {pieces}\n "
            )

        writer.writerow(["\n--- MATCH COMPLETE ---"])
        writer.writerow([f"{white_algo} (White) wins: {white_wins}"])
        writer.writerow([f"{black_algo} (Black) wins: {black_wins}"])
        writer.writerow([f"Draws: {draws}"])
        writer.writerow([f"Average game length: {total_moves / games:.1f} moves"])

    print("\n--- MATCH COMPLETE ---")
    print(f"{white_algo} (White) wins: {white_wins}")
    print(f"{black_algo} (Black) wins: {black_wins}")
    print(f"Draws: {draws}")
    print(f"Average game length: {total_moves / games:.1f} moves")

    return {
        "white_wins": white_wins,
        "black_wins": black_wins,
        "draws": draws,
        "avg_moves": total_moves / games,
    }


if __name__ == "__main__":
    run_matchup("mcts", "iddfs", games=20, log_file="new_rollout_changed_changed_mcts_300_iddfs_5_20.csv")
