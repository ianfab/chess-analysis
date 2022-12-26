import argparse
import functools
import os
import sys

from tqdm import tqdm
import chess.pgn


def game_count(filename):
    f = open(filename, "rb")
    bufgen = iter(functools.partial(f.raw.read, 1024 * 1024), b"")
    return sum(buf.count(b"[Event ") for buf in bufgen)


class PrintAllFensVisitor(chess.pgn.BaseVisitor):
    def __init__(self, id):
        super(PrintAllFensVisitor, self).__init__()
        self.fens = []
        self.id = id
        self.game_result = None
        self.white = None
        self.black = None
        self.whiteElo = 0
        self.blackElo = 0

    def visit_header(self, name, value):
        if name == "Result":
            self.game_result = value
        if name == "White":
            self.white = value
        if name == "Black":
            self.black = value
        if name == "WhiteElo":
            self.whiteElo = value
        if name == "BlackElo":
            self.blackElo = value

    def visit_move(self, board, move):
        self.fens.append(
            "{};id {};player {};elo {};result {};ply {};sm {}".format(
                board.fen(), self.id,
                self.white if board.turn else self.black,
                self.whiteElo if board.turn else self.blackElo,
                self.game_result, board.ply(), move)
        )

    def begin_variation(self):
        return chess.pgn.SKIP

    def result(self):
        return self.fens


def write_fens(pgn_file, stream, count):
    with open(pgn_file) as pgn:
        with tqdm(total=game_count(pgn_file)) as pbar:
            cnt = 0
            while True:
                visitor = functools.partial(PrintAllFensVisitor, "{}#{}".format(os.path.basename(pgn_file), pbar.n + 1))
                try:
                    fens = chess.pgn.read_game(pgn, Visitor=visitor)
                except Exception as e:
                    sys.stderr.write("Skipping game {} due to error: {}".format(pbar.n + 1, str(e)) + os.linesep)
                    fens = []
                pbar.update(1)
                if fens is None:
                    break
                elif len(fens) == 0:
                    continue
                else:
                    cnt += 1

                for fen in fens:
                    stream.write(fen + os.linesep)

                if count and cnt > count:
                    break


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-file", help="pgn file")
    parser.add_argument("-c", "--count", type=int, help="max number of games")

    args = parser.parse_args()
    write_fens(args.input_file, sys.stdout, args.count)
