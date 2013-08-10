#!/usr/bin/env python3

import shelve

from glob import glob

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

import plot_helpers

import argparse

parser = argparse.ArgumentParser(description="produce boxplots for sojourn "
                                 "time vs. errors")
parser.add_argument('dataset', help="name of the .tsv file used.")
parser.add_argument('-dn', '--d-over-n', dest="d_over_n", type=float,
                    default=4, help="ratio between disk and network "
                    "bandwidth in the simulated cluster; default is 4")
parser.add_argument('--load', type=float, default=0.9,
                    help="average load in the simulated cluster; default is "
                    "0.9")
parser.add_argument('--paper', dest='for_paper', action='store_const',
                    const=True, default=False, help="render plots with "
                    "LaTeX and output them as "
                    "sojourn-vs-error_DATASET_D-OVER-N_LOAD.pdf")
args = parser.parse_args()

if args.for_paper:
    plot_helpers.config_paper()

glob_str = 'results_{}_[0-9.]*_{}_{}.s'.format(args.dataset, args.d_over_n, args.load)
shelve_files = sorted((float(fname.split('_')[2]), fname)
                      for fname in glob(glob_str))
sigmas = [sigma for sigma, _ in shelve_files]

no_error = ['FIFO', 'PS', 'LAS', 'FSP (no error)', 'SRPT (no error)']
with_error = ['FSP + FIFO', 'FSP + PS', 'SRPT']

no_error_data = [[] for _ in no_error]
with_error_data = [[] for _ in with_error]

for sigma, fname in shelve_files:
    res = shelve.open(fname, 'r')
    for i, scheduler in enumerate(no_error):
        no_error_data[i].append(np.array(res[scheduler]).mean())
    for i, scheduler in enumerate(with_error):
        with_error_data[i].append([r.mean() for r in res[scheduler]])

for scheduler, err_data in zip(with_error, with_error_data):
    plt.figure(scheduler)
    plt.xlabel("$\sigma$")
    plt.ylabel("mean sojourn time (s)")
    xs = list(range(1, len(sigmas) + 1))
    xs[0] -= 1
    xs[-1] += 1
    for noerr_sched, noerr_data, style in zip(no_error, no_error_data,
                                              plot_helpers.cycle_styles()):
        plt.semilogy(xs, noerr_data, style, label=noerr_sched)
    plt.boxplot(err_data)
    plt.xticks(range(1, len(sigmas) + 1), sigmas)
    plt.ylim(min([min(d) for d in no_error_data]) * 0.85,
             max([max(d) for d in no_error_data]) / 0.85)
    plt.legend(loc=2)

    if args.for_paper:
        fmt = 'sojourn-vs-error_{}_{}_{}_{}.pdf'
        fname = fmt.format(scheduler, args.dataset, args.d_over_n, args.load)
        plt.savefig(fname)

if not args.for_paper:
    plt.show()
