import csv
import time
import chess

from engine.chess_engine import ChessEngine

SEARCH_FUNCS = {
    "minimax": lambda engine: engine.find_best_move("minimax"),
    "alphabeta": lambda engine: engine.find_best_move("alphabeta"),
    "iddfs": lambda engine: engine.find_best_move("iddfs"),
    "mcts": lambda engine: engine.find_best_move("mcts"),
}

def play_single_game(white_algo: str, black_algo: str, max_moves=100):
    """
    Plays one AI-vs-AI game and returns:
        result (1 = white win, 0 = draw, -1 = black win)
        moves_played
    """

    engine = ChessEngine()
    engine.reset_to_endgame_position()   # or classic if you want

    move_counter = 0

    while not engine.is_game_over() and move_counter < max_moves:
        if engine.board.turn == chess.WHITE:
            SEARCH_FUNCS[white_algo](engine)
        else:
            SEARCH_FUNCS[black_algo](engine)

        move_counter += 1

    # Determine result
    if engine.board.is_checkmate():
        print(f"Move count: {move_counter}, Winner: {"WHITE" if engine.board.turn==chess.BLACK else "BLACK" } ")
        return (1 if engine.board.turn == chess.BLACK else -1), move_counter

    print("Draw, moves:", move_counter)
    return 0, move_counter   # draw


def run_matchup(white_algo, black_algo, games=100, log_file="results.csv"):
    """
    Runs many games between two agents.
    Saves results to a CSV for later analysis.
    """

    print(f"Running {games} games: {white_algo} (white) vs {black_algo} (black)")

    white_wins = 0
    black_wins = 0
    draws = 0
    total_moves = 0

    # CSV setup
    with open(log_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Game", "WhiteAlgo", "BlackAlgo", "Result", "Moves"])

        for g in range(1, games + 1):
            result, moves = play_single_game(white_algo, black_algo)
            total_moves += moves

            if result == 1:
                white_wins += 1
            elif result == -1:
                black_wins += 1
            else:
                draws += 1

            writer.writerow([g, white_algo, black_algo, result, moves])
            print(f"Game {g}/{games}: result={result}  moves={moves}")

        print("\n--- MATCH COMPLETE ---")
        print(f"{white_algo} (White) wins: {white_wins}")
        print(f"{black_algo} (Black) wins: {black_wins}")
        print(f"Draws: {draws}")
        print(f"Average game length: {total_moves / games:.1f} moves")

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
    # Example: AlphaBeta vs Minimax, 50 games
    run_matchup("alphabeta", "mcts", games=20, log_file="ab_mcts_20.csv")
    #play_single_game("alphabeta", "minimax")
