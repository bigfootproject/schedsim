#!/usr/bin/env python3

from __future__ import division

import shelve

from glob import glob

import numpy as np
import matplotlib.pyplot as plt

import plot_helpers
import swim_parser

import argparse

NPOINTS = 100000

parser = argparse.ArgumentParser(description="produce CDFs for slowdown "
                                 "vs. error")
parser.add_argument('dataset', help="name of the schedule file used or "
                    "TSV dataset.")
parser.add_argument('--tsv', default=False, action='store_true',
                    help="Read results produced from a SWIM .tsv file")
parser.add_argument('--fname',
                    help="fetch the results from this file. "
                    "Needed unless --tsv is set")
parser.add_argument('--sigma', type=float, default=0.5, help="sigma parameter "
                    "for the log-normal error function; default is 0.5. "
                    "Ignored unless --tsv is set")
parser.add_argument('-dn', '--d-over-n', dest="d_over_n", type=float,
                    default=4.0, help="ratio between disk and network "
                    "bandwidth in the simulated cluster; default is 4. "
                    "Ignored unless --tsv is set")
parser.add_argument('--load', type=float, default=0.9,
                    help="average load in the simulated cluster; default is "
                    "0.9. Ignored unless --tsv is set")
parser.add_argument('--paper', dest='for_paper', action='store_const',
                    const=True, default=False, help="render plots with "
                    "LaTeX and output them as "
                    "sojourn-vs-error_DATASET_SIGMA_D-OVER-N.pdf")
args = parser.parse_args()

if args.for_paper:
    plot_helpers.config_paper()

if not args.fname:
    fname_fmt = 'results_{}_{}_{}_{}.s'
    fname = fname_fmt.format(args.dataset, args.sigma, args.d_over_n, args.load)
else:
    fname = args.fname

no_error = ['FIFO', 'PS', 'LAS', 'FSP (no error)', 'SRPT (no error)']
with_error = ['LAS', 'FSP + FIFO', 'FSP + PS', 'SRPT',
              'SRPT + PS', 'FSP + LAS', 'SRPT + LAS']

if args.tsv:
    workload_fname = '{}.tsv'.format(args.dataset)
    workload = swim_parser.parse_swim(workload_fname, args.d_over_n, args.load)
else:
    with open(args.dataset) as f:
        workload = (line.strip().split() for line in f)
        workload = [(jobid, float(t), float(size))
                    for jobid, t, size in workload]

job_multipliers = np.array([1 / size if size else 0 for _, _, size in workload])

no_error_data = []
with_error_data = []

def samples(results):
    slowdowns = (job_multipliers * results).ravel()
    slowdowns.sort()
    sample_points = np.linspace(0, len(slowdowns) - 1, NPOINTS)
    return slowdowns[np.round(sample_points).astype(int)]
    

res = shelve.open(fname, 'r')
for scheduler in no_error:
    no_error_data.append(samples(res[scheduler]))
for scheduler in with_error:
    with_error_data.append(samples(res[scheduler]))

figures = [("No error", float(0), no_error, no_error_data),
           (r"$\sigma={}$".format(args.sigma),
            args.sigma, with_error, with_error_data)]

for title, sigma, schedulers, data in figures:
    plt.figure(title)
    plt.xlabel("Slowdown")
    plt.ylabel("ECDF")
    ys = np.linspace(1 / NPOINTS, 1, NPOINTS)

    for scheduler, xs, style in zip(schedulers, data,
                                    plot_helpers.cycle_styles()):
        # plot the CDF of results
        plt.semilogx(xs, ys, label=scheduler)
    plt.grid()
    plt.legend(loc=0)

    if args.for_paper:
        fmt = 'slowdown_{}_{}_{}_{}.pdf'
        fname = fmt.format(args.dataset, sigma, args.d_over_n, args.l)
        plt.savefig(fname)

if not args.for_paper:
    plt.show()
