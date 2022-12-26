import argparse
import asyncio
import fileinput
from functools import partial

import chess
import chess.engine
from tqdm import tqdm

from common import parse_epd, sum_line_count


def line_count(filename):
    with open(filename, 'rb') as f:
        bufgen = iter(partial(f.raw.read, 1024*1024), b'')
        return sum(buf.count(b'\n') for buf in bufgen)


async def analyze(engine, board, move, depth):
    multipv_info = await engine.analyse(board, chess.engine.Limit(depth=depth, ensuremove=move), multipv=2)
    index = [i for i, d in enumerate(multipv_info) if d["pv"][0] == move]
    assert len(index) == 1, print([d["pv"] for d in multipv_info])
    return {
        "bm": multipv_info[0]["pv"][0],
        "ce": multipv_info[0]["score"].relative.score(mate_score=100000),
        "ce2": multipv_info[index[0]]["score"].relative.score(mate_score=100000),
        "acd": depth
    }


async def main(instream, engine_path, depth) -> None:
    transport, engine = await chess.engine.popen_uci(engine_path)

    total = sum_line_count(instream)
    for epd in tqdm(instream, total=total):
        fen, annotations = parse_epd(epd)
        board = chess.Board(fen=fen)
        move = chess.Move.from_uci(annotations["sm"])
        annotations.update(await analyze(engine, board, move, depth))
        print(fen + "".join(";{} {}".format(k, v) for k, v in annotations.items()))

    await engine.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('epd_files', nargs='*')
    parser.add_argument("-e", "--engine", required=True)
    parser.add_argument("-d", "--depth", type=int, default=5)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)

    asyncio.set_event_loop_policy(chess.engine.EventLoopPolicy())
    with fileinput.input(args.epd_files) as instream:
        asyncio.run(main(instream, args.engine, args.depth))
