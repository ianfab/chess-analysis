# Chess analysis

This project analyses chess games using Stockfish and python-chess.

## Process
1. `pgn2epd.py` generates an EPD file from a given PGN.
2. `analyze.py` analyzes the positions from an EPD file.
3. `evaluate.py` evaluates analyzed positions according to a given model.

## Setup
The scripts require python3 as well as the dependencies from the `requirements.txt`. Install them using
```
pip3 install -r requirements.txt
```
