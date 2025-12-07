# Endgame Chess – CS246 AI Project

This project implements a chess engine, several AI search algorithms, and a Tkinter-based user interface for testing AI vs AI performance in endgame positions. The engine uses python-chess for board representation and legal move generation. All experiment scripts are located in the `tournament/` directory.

## Project Structure

cs246-chess-ai/
├─ ai/             search algorithms and evaluation
├─ analysis/       analysis scripts and charts
├─ config/         configuration constants
├─ engine/         engine and game logic
├─ tournament/     AI vs AI scripts and endgame positions
├─ ui/             Tkinter user interface
└─ main.py         GUI entry point

## Run the UI

From the project root directory:

python main.py

The UI provides three modes:
- Human vs Human
- Human vs AI
- AI vs AI

Algorithm and search depth can be selected in the start menu.

## Run AI vs AI Experiments

From the project root directory:

### Random endgame positions
python -m tournament.ai_vs_ai

### Fixed endgame positions
python -m tournament.ai_vs_ai_fixed

### Draw reason analysis
python -m tournament.ai_vs_ai_draw_reasons
