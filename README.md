# Chess analysis

This project analyses chess games using Stockfish and python-chess, and aggregates statistics such as ACPL and related metrics using pandas.

This can be either used to analyze the quality of play depending on various properties such as Elo, player, etc., or to evaluate the metrics themselves against objective quality of play indicators such as Elo and result.

## Process
1. `pgn2epd.py` generates an EPD file from a given PGN.
2. `analyze.py` analyzes positions from an EPD file and annotates them.
3. `stats.py` aggregates statistics from an annotated EPD file.

## Setup
The scripts require python3 as well as the dependencies from the `requirements.txt`. Install them using
```
pip3 install -r requirements.txt
```
In order to ensure that best and player moves are evaluated within the same search, a [custom version of stockfish](https://github.com/ianfab/Stockfish/tree/ensuremove) and [python-chess](https://github.com/ianfab/python-chess/tree/ensuremove) are used that support this feature.

## Output
The main focus of this project is to quantify quality of play using various metrics comparable to but different from average centipawn loss (ACPL). Metrics can have different strengths and weaknesses depending on their design, e.g.:
* Weighting: Metrics such as (uncapped) ACPL can give extremely large weight to single moves compared to the rest of a game, which can skew results.
* Bias: Using summative metrics can lead to a strong correlation with game length, which is undesirable.
* Exploitability: Using averaging can make metrics susceptible to biases by long sequences of moves not affecting the result, e.g., playing on in dead drawn or losing positions.

Some ways to attempt to make metrics more robust are:
* Capping values/differences can limit the influence of a single move.
* Using expectation values (EV) and their differences (expected loss, EL) instead of raw centipawn (loss) values transforming to a limited range mitigates the weighting problem.
* Normalizing by the potential for loss, e.g., dividing by the maximum possible loss, leads to more equal weighting of decisions.

Some abbreviations used in the names of metrics:
* base metric
  * CP/CPL: centipawn / centipawn loss
  * EV/EL: expectation value / expected loss
* transformation
  * C: capped
  * SF: stockfish win-rate model
  * L: lichess win-rate model
* aggregation
  * T: total
  * A: average
  * N: normalized
  * EW: equal weighted
