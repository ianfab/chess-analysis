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


def get_score(result, color):
    return {"1-0": 1, "0-1": 0}.get(result if color == "w" else result[::-1], 0.5)


def main(instream) -> None:
    stats = []
    total = sum_line_count(instream)
    for epd in tqdm(instream, total=total):
        fen, annotations = parse_epd(epd)
        annotations["color"] = fen.split()[1]
        stats.append(annotations)
    df = pd.DataFrame(stats).astype(
        {
            "elo": "int",
            "ply": "int",
            "ce": "int",
            "ce2": "int",
        }
    )
    df["bestmove"] = df["sm"] == df["bm"]
    df["cpl"] = df.apply(lambda x: get_cpl(x["ce"], x["ce2"]), axis=1)
    df["el_sf"] = df.apply(lambda x: get_el(x["ce"], x["ce2"], "sf", x["ply"]), axis=1)
    df["el_l"] = df.apply(lambda x: get_el(x["ce"], x["ce2"], "lichess", x["ply"]), axis=1)
    df["score"] = df.apply(lambda x: get_score(x["result"], x["color"]), axis=1)
    df["cpl2"] = df["cpl"]
    df.loc[df["ce"] < -1000, "cpl2"] = np.nan
    print("# Raw data")
    print(df)
    columns = ["elo", "bestmove", "cpl", "el_sf", "el_l"]
    aggs = ["mean"]
    with pd.option_context('display.float_format', '{:.3f}'.format):
        print("# General stats")
        print("## move stats aggregated by rating range")
        print(df.groupby(pd.cut(df["elo"], np.arange(1200, 3000, 100)))[columns].agg(aggs))
        print("## move stats aggregated by game ply")
        print(df.groupby(pd.cut(df["ply"], np.arange(0, 200, 10)))[columns].agg(aggs))
        print("## move stats aggregated by current centipawn evaluation")
        print(df.groupby(pd.cut(df["ce"], np.arange(-1000, 1000, 100)))[columns].agg(aggs))
    with pd.option_context('display.float_format', '{:.4f}'.format):
        per_player_game = df.groupby(["player", "id"]).agg(
            elo=("elo", "mean"),
            score=("score", "mean"),
            moves=("id", "count"),
            bestmove=("bestmove", "mean"),
            acpl=("cpl", "mean"),
            acpl2=("cpl2", "mean"),
            tel_sf=("el_sf", "sum"),
            ael_sf=("el_sf", "mean"),
            tel_l=("el_l", "sum"),
            ael_l=("el_l", "mean"),
        )
        print("## game stats correlation")
        print("### Pearson")
        print(per_player_game.corr(method="pearson"))
        print("### Spearman")
        print(per_player_game.corr(method="spearman"))
        print()
        print("# Player stats")
        print("## stats aggregated per player and game")
        print(per_player_game)
        # by player
        print("## move stats aggregated per player")
        print(df.groupby("player")[columns].agg(aggs))
        print("## game stats aggregated per player")
        print(per_player_game.groupby(["player"]).agg(["mean"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("epd_files", nargs="*")
    args = parser.parse_args()

    with fileinput.input(args.epd_files) as instream:
        main(instream)
