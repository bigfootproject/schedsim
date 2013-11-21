#!/usr/bin/env python3

import shelve

from glob import glob

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

import plot_helpers

import argparse

parser = argparse.ArgumentParser(description="produce boxplots for sojourn "
                                 "time vs. d/n")
parser.add_argument('dataset', help="name of the .tsv file used.")
parser.add_argument('sigma', type=float, help="sigma parameter for the "
                    "log-normal error function")
parser.add_argument('--load', type=float, default=0.9,
                    help="average load in the simulated cluster; default is "
                    "0.9")
parser.add_argument('--paper', dest='for_paper', action='store_const',
                    const=True, default=False, help="render plots with "
                    "LaTeX and output them as "
                    "sojourn-vs-error_DATASET_SIGMA_LOAD.pdf")
args = parser.parse_args()

if args.for_paper:
    plot_helpers.config_paper()

glob_str = 'results_{}_{}_[0-9.]*_{}.s'.format(args.dataset, args.sigma,
                                               args.load)
shelve_files = sorted((float(fname.split('_')[3]), fname)
                      for fname in glob(glob_str))
dns = [dn for dn, _ in shelve_files]

no_error = ['FIFO', 'PS', 'LAS', 'FSP (no error)', 'SRPT (no error)']
with_error = ['FIFO', 'PS', 'LAS', 'FSP + FIFO', 'FSP + PS', 'SRPT',
              'SRPT + PS', 'FSP + LAS']

no_error_data = [[] for _ in no_error]
with_error_data = [[] for _ in with_error]

for dn, fname in shelve_files:
    res = shelve.open(fname, 'r')
    for i, scheduler in enumerate(no_error):
        no_error_data[i].append(np.array(res[scheduler]).mean())
    for i, scheduler in enumerate(with_error):
        with_error_data[i].append(np.array(res[scheduler]).mean())

figures = [("No error", float(0), no_error, no_error_data),
           (r"$\sigma={}$".format(args.sigma), args.sigma, with_error, with_error_data)]

for title, sigma, schedulers, data in figures:
    plt.figure(title)
    plt.xlabel("$d/n$")
    plt.ylabel("mean sojourn time (s)")

    for scheduler, mst, style in zip(schedulers, data,
                                     plot_helpers.cycle_styles('x')):
        plt.semilogy(dns, mst, style, label=scheduler)
    plt.grid()
    plt.legend(loc=2)

    if args.for_paper:
        fmt = 'sojourn-vs-dn_{}_{}_{}.pdf'
        fname = fmt.format(args.dataset, sigma, args.load)
        plt.savefig(fname)

if not args.for_paper:
    plt.show()
