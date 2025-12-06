BOARD_SIZE = 8
SQUARE_SIZE = 80


PIECE_SETS = {
    "Unicode": {
        "wK": "♔", "wQ": "♕", "wR": "♖", "wB": "♗", "wN": "♘", "wP": "♙",
        "bK": "♚", "bQ": "♛", "bR": "♜", "bB": "♝", "bN": "♞", "bP": "♟",
    },
    "Letters": {
        "wK": "K", "wQ": "Q", "wR": "R", "wB": "B", "wN": "N", "wP": "P",
        "bK": "k", "bQ": "q", "bR": "r", "bB": "b", "bN": "n", "bP": "p",
    },
}


PIECE_VALUES = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 0}

THEMES = {
    "Classic": {
        "light": "#EEEED2",
        "dark": "#769656",
        "highlight": "#BACA44",
        "selected": "#F6F669",
        "last_move": "#F3E99F",
    },
    "Dark": {
        "light": "#B0B0B0",
        "dark": "#404040",
        "highlight": "#6D8F1F",
        "selected": "#D4D24C",
        "last_move": "#595959",
    },
    "Ocean": {
        "light": "#E6F4F1",
        "dark": "#2F6F7E",
        "highlight": "#4BA3C3",
        "selected": "#8ED8F4",
        "last_move": "#71BFD8",
    },
    "Candy": {
        "light": "#FFE4F2",
        "dark": "#C471ED",
        "highlight": "#F9A8D4",
        "selected": "#FDE68A",
        "last_move": "#FBCFE8",
    },
    "Sunset": {
        "light": "#FDEBD0",
        "dark": "#C4563F",
        "highlight": "#F5CBA7",
        "selected": "#F9E79F",
        "last_move": "#FAD7A0",
    },
    "Galaxy": {
        "light": "#2F3640",
        "dark": "#192A56",
        "highlight": "#00A8FF",
        "selected": "#9C88FF",
        "last_move": "#273C75",
    },
}
