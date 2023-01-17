import argparse
import fileinput

from chess.engine import Cp
from tqdm import tqdm
import numpy as np
import pandas as pd

from common import parse_epd, sum_line_count


def get_ev(cp, model, ply) -> float:
    return Cp(cp).wdl(model=model, ply=ply).expectation()


def get_el(ce, ce2, model, ply) -> float:
    return get_ev(ce, model, ply) - get_ev(ce2, model, ply)


def clamp(v, vmax):
    return min(max(v, -vmax), vmax)


def get_cpl(ce, ce2, cap=1000) -> int:
    return clamp(ce, cap) - clamp(ce2, cap)


def get_stats(ce, ce2, ply) -> tuple:
    return {
        "el_sf": get_el(ce, ce2, "sf", ply),
        "el_l": get_el(ce, ce2, "lichess", ply),
        "cpl": get_cpl(ce, ce2),
    }


def main(instream) -> None:
    stats = []
    total = sum_line_count(instream)
    for epd in tqdm(instream, total=total):
        _, annotations = parse_epd(epd)
        stats_entry = get_stats(int(annotations["ce"]), int(annotations["ce2"]), int(annotations["ply"]))
        stats_entry.update(annotations)
        stats.append(stats_entry)
    df = pd.DataFrame(stats).astype(
        {
            "elo": "int",
            "ply": "int",
            "ce": "int",
            "ce2": "int"
        }
    )
    columns = ["elo", "cpl", "el_sf", "el_l"]
    aggs = ["mean", "std"]
    with pd.option_context('display.float_format', '{:.3f}'.format):
        print("# General stats")
        # by rating range
        print(df.groupby(pd.cut(df["elo"], np.arange(1200, 3000, 100)))[columns].agg(aggs))
        # by ply
        print(df.groupby(pd.cut(df["ply"], np.arange(0, 200, 10)))[columns].agg(aggs))
        # by ce
        print(df.groupby(pd.cut(df["ce"], np.arange(-1000, 1000, 100)))[columns].agg(aggs))
        print()
        print("# Player stats")
    with pd.option_context('display.float_format', '{:.4f}'.format):
        # per player and game
        per_player_game = df.groupby(["player", "id"]).agg(
            elo=("elo", "mean"),
            moves=("id", "count"),
            tel_sf=("el_sf", "sum"),
            ael_sf=("el_sf", "mean"),
            tel_l=("el_l", "sum"),
            ael_l=("el_l", "mean"),
        )
        print(per_player_game)
        # by player
        print(df.groupby("player")[columns].agg(aggs))
        print(per_player_game.groupby(["player"]).agg(["mean"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("epd_files", nargs="*")
    args = parser.parse_args()

    with fileinput.input(args.epd_files) as instream:
        main(instream)
