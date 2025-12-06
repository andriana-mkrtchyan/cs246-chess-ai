import chess
import random
import math
from ai.evaluation import evaluate_position as evaluate


def minimax(board, depth, maximizing):
    """Return the minimax evaluation and best move for the given depth."""
    if depth == 0 or board.is_game_over():
        return evaluate(board), None

    best_move = None

    if maximizing:
        max_eval = -float("inf")
        for move in board.legal_moves:
            board.push(move)
            eval_score, _ = minimax(board, depth - 1, False)
            board.pop()

            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move

        return max_eval, best_move

    else:
        min_eval = float("inf")
        for move in board.legal_moves:
            board.push(move)
            eval_score, _ = minimax(board, depth - 1, True)
            board.pop()

            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move

        return min_eval, best_move


def alpha_beta(board, depth, alpha, beta, maximizing):
    """Return alpha-beta evaluation with quiescence and the selected move."""
    if depth == 0 or board.is_game_over():
        return quiescence(board, alpha, beta, maximizing), None

    best_move = None

    if maximizing:
        max_eval = -float("inf")
        for move in board.legal_moves:
            board.push(move)

            eval_score, _ = alpha_beta(board, depth - 1, alpha, beta, False)
            board.pop()

            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move

            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break

        return max_eval, best_move

    else:
        min_eval = float("inf")
        for move in board.legal_moves:
            board.push(move)

            eval_score, _ = alpha_beta(board, depth - 1, alpha, beta, True)
            board.pop()

            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move

            beta = min(beta, eval_score)
            if beta <= alpha:
                break

        return min_eval, best_move


class MCTSNode:
    """A node in the Monte Carlo Tree Search structure."""

    def __init__(self, board, parent=None, move=None):
        self.board = board            # current state
        self.parent = parent          # parent node
        self.move = move              # move leading to this node
        self.children = []            # child nodes
        self.untried = list(board.legal_moves)

        self.visits = 0               # number of visits
        self.value = 0.0              # accumulated value from root perspective

    def uct(self, c=1.41):
        """Return the UCT score for node selection."""
        if self.visits == 0:
            return float("inf")
        return (self.value / self.visits) + c * math.sqrt(
            math.log(self.parent.visits + 1) / self.visits
        )


def rollout(board, root_color, depth=20):
    """Perform a rollout from the given board and return a normalized result."""
    for _ in range(depth):
        if board.is_game_over():
            if board.is_checkmate():
                loser = board.turn
                winner = not loser
                return 10 if winner == root_color else -10
            return 0

        moves = list(board.legal_moves)

        captures = [m for m in moves if board.is_capture(m)]
        if captures and random.random() < 0.5:
            move = random.choice(captures)
        else:
            move = random.choice(moves)

        board.push(move)

    score = evaluate(board)
    score = max(-2, min(2, score))  # clamp
    score /= 2

    return score if root_color == chess.WHITE else -score


def mcts(board, simulations=400):
    """Run Monte Carlo Tree Search and return the selected move."""
    root = MCTSNode(board.copy())
    root_color = board.turn

    for _ in range(simulations):
        node = root

        # Selection
        while not node.untried and node.children:
            node = max(node.children, key=lambda n: n.uct())

        # Expansion
        if node.untried:
            move = node.untried.pop()
            new_board = node.board.copy()
            new_board.push(move)

            child = MCTSNode(new_board, parent=node, move=move)
            node.children.append(child)
            node = child

        # Simulation
        result = rollout(node.board.copy(), root_color=root_color)

        # Backpropagation
        while node:
            node.visits += 1
            node.value += result
            node = node.parent

    best_child = max(root.children, key=lambda n: n.visits)
    return best_child.move


def iterative_deepening(board, max_depth):
    """Run iterative deepening alpha-beta up to max_depth and return the best move."""
    best = None
    maximizing = board.turn == chess.WHITE
    for depth in range(1, max_depth + 1):
        _, best = alpha_beta(board, depth, -float("inf"), float("inf"), maximizing)
    return best


def iddfs_alphabeta_move(board, max_depth: int = 6):
    """Return a move computed with iterative deepening using alpha-beta search."""
    return iterative_deepening(board, max_depth)


def quiescence(board, alpha, beta, maximizing):
    """
    Perform quiescence search to avoid horizon effects.

    The evaluation is from White's perspective:
    positive is good for White, negative is good for Black.
    """
    stand_pat = evaluate(board)

    if maximizing:
        if stand_pat >= beta:
            return stand_pat
        if stand_pat > alpha:
            alpha = stand_pat
    else:
        if stand_pat <= alpha:
            return stand_pat
        if stand_pat < beta:
            beta = stand_pat

    for move in board.legal_moves:
        if not board.is_capture(move):
            continue

        board.push(move)
        score = quiescence(board, alpha, beta, not maximizing)
        board.pop()

        if maximizing:
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break
        else:
            if score < beta:
                beta = score
            if alpha >= beta:
                break

    return alpha if maximizing else beta
