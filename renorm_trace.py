#!/usr/bin/env python3

import argparse
import sys

import numpy as np

parser = argparse.ArgumentParser(description="Renormalize trace by scaling "
                                 "job size to obtain the desired load; "
                                 "shift submission times to have the first "
                                 "value at 0")
parser.add_argument('load', type=float, help="desired load")
parser.add_argument('--input', help="input file (stdin if omitted)")
parser.add_argument('--output', help="output file (stdout if omitted)")
args = parser.parse_args()

schedule = np.loadtxt(args.input if args.input is not None else sys.stdin)

schedule[:, 0] -= schedule[0, 0]
schedule[:, 1] *= schedule[-1, 0] * args.load / schedule[:, 1].sum()

np.savetxt(args.output if args.output is not None else sys.stdout,
           schedule)
