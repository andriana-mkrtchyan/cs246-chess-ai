import chess
import random
import math
from ai.evaluation import  evaluate_position as evaluate



# ============================================================
# PURE MINIMAX
# ============================================================

def minimax(board, depth, maximizing):
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


# ============================================================
# MINIMAX WITH ALPHA-BETA + QUIESCENCE
# ============================================================

def alpha_beta(board, depth, alpha, beta, maximizing):
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



# ============================================================
# MONTE CARLO TREE SEARCH (basic)
# ============================================================
class MCTSNode:
    def __init__(self, board, parent=None, move=None):
        self.board = board            # state
        self.parent = parent          # parent node
        self.move = move              # move that led here
        self.children = []            # list of child nodes
        self.untried = list(board.legal_moves)  # moves not yet expanded

        self.visits = 0               # N(s)
        self.value = 0.0              # Q(s), cumulative root-perspective score


    # UCT formula (root-perspective value)
    def uct(self, c=1.41):
        if self.visits == 0:
            return float("inf")
        return (self.value / self.visits) + c * math.sqrt(
            math.log(self.parent.visits + 1) / self.visits
        )


# ============================================================
# SIMULATION (Rollout)
# ============================================================
def rollout(board, root_color, depth=20):
    for _ in range(depth):
        if board.is_game_over():
            if board.is_checkmate():
                loser = board.turn
                winner = not loser
                return 10 if winner == root_color else -10
            return 0

        moves = list(board.legal_moves)

        # slightly biased randomness
        captures = [m for m in moves if board.is_capture(m)]
        if captures and random.random() < 0.5:
            move = random.choice(captures)
        else:
            move = random.choice(moves)

        board.push(move)

    # evaluation cutoff
    score = evaluate(board)

    # normalization to [-1, 1] scale
    score = max(-2, min(2, score))
    score /= 2

    return score if root_color == chess.WHITE else -score

# ============================================================
# MAIN MCTS
# ============================================================

def mcts(board, simulations=400):
    root = MCTSNode(board.copy())
    root_color = board.turn  # who the final score is measured for

    for _ in range(simulations):
        node = root

        # --------------------------
        # 1. SELECTION (UCT)
        # --------------------------
        while not node.untried and node.children:
            node = max(node.children, key=lambda n: n.uct())

        # --------------------------
        # 2. EXPANSION
        # --------------------------
        if node.untried:
            move = node.untried.pop()
            new_board = node.board.copy()
            new_board.push(move)

            child = MCTSNode(new_board, parent=node, move=move)
            node.children.append(child)
            node = child

        # --------------------------
        # 3. SIMULATION / ROLLOUT
        # --------------------------
        result = rollout(node.board.copy(), root_color=root_color)

        # --------------------------
        # 4. BACKPROPAGATION
        #    Reward stays ROOT-PERSPECTIVE
        # --------------------------
        while node:
            node.visits += 1
            node.value += result
            node = node.parent

    # Choose move with highest visit count (robust child)
    best_child = max(root.children, key=lambda n: n.visits)
    return best_child.move

# class MCTSNode:
#     def __init__(self, board, parent=None):
#         self.board = board
#         self.parent = parent
#         self.children = []
#         self.untried = list(board.legal_moves)
#         self.visits = 0
#         self.value = 0
#
#     def uct(self, c=1.41):
#         if self.visits == 0:
#             return float("inf")
#         return (self.value / self.visits) + c * math.sqrt(
#             math.log(self.parent.visits) / self.visits
#         )
#
#
# def simulate(board, root_color):
#     """Rollout: random game until terminal state."""
#     while not board.is_game_over():
#         move = random.choice(list(board.legal_moves))
#         board.push(move)
#
#     if board.is_checkmate():
#         loser = board.turn
#         winner = not loser
#         return 1 if winner == root_color else -1
#     return 0
#
#
# def mcts(board, simulations=200):
#     root = MCTSNode(board.copy())
#     root_color = board.turn
#
#     for _ in range(simulations):
#         node = root
#
#         # Selection
#         while not node.untried and node.children:
#             node = max(node.children, key=lambda n: n.uct())
#
#         # Expansion
#         if node.untried:
#             move = node.untried.pop()
#             new_board = node.board.copy()
#             new_board.push(move)
#             child = MCTSNode(new_board, parent=node)
#             node.children.append(child)
#             node = child
#
#         # Simulation
#         result = simulate(node.board.copy(), root_color=root_color)
#
#         # Backpropagation
#         while node:
#             node.visits += 1
#             node.value += result
#             result = -result
#             node = node.parent
#
#     best_child = max(root.children, key=lambda n: n.visits)
#     return best_child.board.move_stack[-1]

# ============================================================
# ITERATIVE DEEPENING (wraps ab)
# ============================================================

def iterative_deepening(board, max_depth):
    best = None
    maximizing = board.turn == chess.WHITE
    for depth in range(1, max_depth + 1):
        _, best = alpha_beta(board, depth, -float("inf"), float("inf"), maximizing)
    return best

def iddfs_alphabeta_move(board, max_depth: int = 6):
    """
    Wrapper around iterative_deepening so we can use it as a separate algorithm
    in experiments (e.g., algo_name == 'iddfs_ab').

    Uses alpha-beta + quiescence internally, searching depth 1..max_depth.
    """
    return iterative_deepening(board, max_depth)

# ============================================================
# QUIESCENCE SEARCH
# ============================================================

def quiescence(board, alpha, beta, maximizing):
    """
    Quiescence search in minimax style.

    - evaluate(board) is from White's perspective:
      positive = good for White, negative = good for Black.
    - 'maximizing = True' means the current player is trying
      to increase this score (i.e., White at root),
      'maximizing = False' means trying to decrease it.
    """
    stand_pat = evaluate(board)

    if maximizing:
        # If even the "stand pat" score is too good, prune.
        if stand_pat >= beta:
            return stand_pat
        if stand_pat > alpha:
            alpha = stand_pat
    else:
        # Minimizing: if stand_pat already too low, prune.
        if stand_pat <= alpha:
            return stand_pat
        if stand_pat < beta:
            beta = stand_pat

    # Only search capture moves to remove noisy tactical swings.
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
                break  # beta cutoff
        else:
            if score < beta:
                beta = score
            if alpha >= beta:
                break  # alpha cutoff

    return alpha if maximizing else beta


