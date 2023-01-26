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
    df["cpl"] = df["ce"].clip(-1000, 1000) - df["ce2"].clip(-1000, 1000)
    df["el_sf"] = df.apply(lambda x: get_el(x["ce"], x["ce2"], "sf", x["ply"]), axis=1)
    df["ev_l"] = df.apply(lambda x: get_ev(x["ce"], "lichess", x["ply"]), axis=1)
    df["el_l"] = df.apply(lambda x: get_el(x["ce"], x["ce2"], "lichess", x["ply"]), axis=1)
    df["score"] = ((df["color"] == "b").astype(float) - df["result"].map({"1-0": 1, "0-1": 0, "1/2-1/2": 0.5})).abs()
    df["test1"] = df["cpl"].clip(-200, 200)
    df.loc[df["ce"] < -500, "test1"] = np.nan
    df["test2"] = df["el_l"]
    df.loc[df["ce"] < -300, "test2"] = np.nan
    df["test3"] = df["el_l"] / df["ev_l"]
    df.loc[df["ce"] < -300, "test3"] = np.nan
    df["test4"] = df["el_l"]
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
            tel_sf=("el_sf", "sum"),
            ael_sf=("el_sf", "mean"),
            tel_l=("el_l", "sum"),
            ael_l=("el_l", "mean"),
            aev_l=("ev_l", "mean"),
            test1=("test1", "mean"),
            test2=("test2", "mean"),
            test3=("test3", "mean"),
            test4=("test4", "mean"),
        )
        per_player_game["test4"] = per_player_game["test4"] / per_player_game["aev_l"]
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
