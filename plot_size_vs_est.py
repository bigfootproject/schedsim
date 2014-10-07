#!/usr/bin/env python3

import argparse

import numpy

from matplotlib import cm
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description="Job size vs. estimation")
parser.add_argument('file', help="file with the workload")
parser.add_argument('--nolatex', default=False, action='store_true',
                    help="disable LaTeX rendering")
parser.add_argument('--save', help="don't show but save in target filename")
args = parser.parse_args()

_, sizes, bytes = numpy.loadtxt(args.file).T

plt.figure(figsize=(8, 4.5))
plt.xlabel("Data size (bytes)")
plt.ylabel("Job size (s)")
plt.tick_params(axis='x', pad=7)

plt.hexbin(bytes + 1, (sizes + 1) / 1000, xscale='log', yscale='log',
           bins='log', cmap=cm.Reds)

if not args.nolatex:
    import plot_helpers
    plot_helpers.config_paper(20)

plt.tight_layout(1)

if args.save is not None:
    plt.savefig(args.save)
else:
    plt.show()
