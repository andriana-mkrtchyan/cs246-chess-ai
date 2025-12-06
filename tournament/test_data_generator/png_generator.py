import csv
import chess
import chess.svg
from pathlib import Path

def load_fens_from_csv(path):
    fens = []
    with open(path, "r", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for row in reader:
            if not row:
                continue
            fens.append(row[1])
    return fens


def generate_svg_boards(fen_file, out_dir="fen_svgs"):
    fens = load_fens_from_csv(fen_file)
    out_path = Path(out_dir)
    out_path.mkdir(exist_ok=True)

    for idx, fen in enumerate(fens, start=1):
        board = chess.Board(fen)
        svg_code = chess.svg.board(board=board)

        file_path = out_path / f"fen_{idx}.svg"
        file_path.write_text(svg_code, encoding="utf-8")
        print(f"Saved: {file_path}")


if __name__ == "__main__":
    generate_svg_boards("../endgame_positions.csv")

