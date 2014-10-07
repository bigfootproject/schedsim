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
parser.add_argument('--renorm_estimations', choices=['proportional', 'total'],
                    help="renormalize the estimations as well: if "
                    "'proportional', they will be rescaled by the same factor "
                    "of sizes; if 'total', the sum of estimations will "
                    "be equal to the sum of job sizes")
args = parser.parse_args()

schedule = np.loadtxt(args.input if args.input is not None else sys.stdin)

schedule[:, 0] -= schedule[0, 0]
factor = schedule[-1, 0] * args.load / schedule[:, 1].sum()
schedule[:, 1] *= factor
if args.renorm_estimations == 'proportional':
    schedule[:, 2] *= factor
elif args.renorm_estimations == 'total':
    schedule[:, 2] *= schedule[:, 1].sum() / schedule[:, 2].sum()

np.savetxt(args.output if args.output is not None else sys.stdout,
           schedule)
