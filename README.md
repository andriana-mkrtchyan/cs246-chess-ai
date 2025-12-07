Endgame Chess – CS246 AI Project

This project implements a chess engine, multiple AI search algorithms, and a Tkinter UI for testing AI vs AI performance in endgame positions.

The engine uses python-chess for board representation and legal move generation.
All experiment scripts are located inside the tournament/ folder.

📂 Project Structure
cs246-chess-ai/
├─ ai/             # search algorithms and evaluation
├─ analysis/       # analysis scripts + charts
├─ config/         # global constants
├─ engine/         # board state, legality, moves
├─ tournament/     # AI vs AI experiment scripts + endgame positions
├─ ui/             # Tkinter GUI
└─ main.py         # GUI entry point

▶️ Run the UI (Play Mode)

From the project root:

python main.py


This opens the UI menu where you can choose:

Human vs Human

Human vs AI

AI vs AI
and select algorithm + depth.

To make the AI respond in Human vs AI, press AI Move.

🧪 Run Experiments (AI vs AI)

All experiments are executed from the project root.

1. AI vs AI — Random Endgame Positions

Runs matches on randomly generated endgame states.

python -m tournament.ai_vs_ai

2. AI vs AI — Fixed Endgame Positions

Runs the same matches using fixed FEN positions from tournament/endgame_positions.csv.

python -m tournament.ai_vs_ai_fixed

3. AI vs AI — Draw Reason Analysis

Analyses why matches end in draws (stalemate, threefold, insufficient material, etc.).

python -m tournament.ai_vs_ai_draw_reasons

📊 Output

Experiment logs are written to CSV files.

Analysis and charts (if generated separately) appear in:

analysis/charts/

👥 Authors

CS246 – Artificial Intelligence
American University of Armenia
Group Project by:
Liza Khachatryan Norayr Amirkhanyan, Andriana Mkrtchyan
