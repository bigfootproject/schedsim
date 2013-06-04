#!/usr/bin/env python3

import shelve
import sys

from glob import glob
from itertools import cycle

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

dataset, sigma, load = sys.argv[1:4]
sigma = float(sigma)
load = float(load)

for_paper = len(sys.argv) >= 5 and sys.argv[4] == 'paper'

if for_paper:
    matplotlib.rc('font',**{'family':'serif','serif':['Palatino']})
    matplotlib.rc('text', usetex=True)
    matplotlib.rcParams.update({'font.size': 22})

glob_str = 'results_{}_{}_[0-9.]*_{}.s'.format(dataset, sigma, load)
shelve_files = sorted((float(fname.split('_')[3]), fname)
                      for fname in glob(glob_str))
dns = [dn for dn, _ in shelve_files]

no_error = ['FIFO', 'PS', 'FSP (no error)', 'SRPT (no error)']
with_error = ['FIFO', 'PS', 'FSP + FIFO', 'FSP + PS', 'SRPT']

no_error_data = [[] for _ in no_error]
with_error_data = [[] for _ in with_error]

for load, fname in shelve_files:
    res = shelve.open(fname, 'r')
    for i, scheduler in enumerate(no_error):
        no_error_data[i].append(np.array(res[scheduler]).mean())
    for i, scheduler in enumerate(with_error):
        with_error_data[i].append(np.array(res[scheduler]).mean())

figures = [("No error", 0, no_error, no_error_data),
           (r"$\sigma={}$".format(sigma), sigma, with_error, with_error_data)]

for title, sigma, schedulers, data in figures:
    plt.figure(title)
    plt.xlabel("$d/n$")
    plt.ylabel("mean sojourn time (s)")
    line_styles = cycle("-x --x -.x :x".split())

    for scheduler, mst in zip(schedulers, data):
        plt.semilogy(dns, mst, next(line_styles), label=scheduler)
    plt.grid()
    plt.legend(loc=2)

    if for_paper:
        fmt = 'sojourn-vs-dn_{}_{}_{}.eps'
        fname = fmt.format(dataset, sigma, load)
        plt.savefig(fname)

if not for_paper:
    plt.show()
