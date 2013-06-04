#!/usr/bin/env python3

import shelve
import sys

from glob import glob
from itertools import cycle

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

dataset, d_over_n, load = sys.argv[1:4]

for_paper = len(sys.argv) >= 5 and sys.argv[4] == 'paper'

if for_paper:
    matplotlib.rc('font',**{'family':'serif','serif':['Palatino']})
    matplotlib.rc('text', usetex=True)
    matplotlib.rcParams.update({'font.size': 22})

glob_str = 'results_{}_[0-9.]*_{}_{}.s'.format(dataset, d_over_n, load)
shelve_files = sorted((float(fname.split('_')[2]), fname)
                      for fname in glob(glob_str))
sigmas = [sigma for sigma, _ in shelve_files]

def avg_sojourn(results, scheduler):
    return np.array(results[scheduler]).mean()

no_error = ['FIFO', 'PS', 'FSP (no error)', 'SRPT (no error)']
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
    xs = range(1, len(sigmas) + 1)
    line_styles = cycle("- -- -. :".split())
    for noerr_sched, noerr_data in zip(no_error, no_error_data):
        plt.semilogy(xs, noerr_data, next(line_styles), label=noerr_sched)
    plt.boxplot(err_data)
    plt.xticks(range(1, len(sigmas) + 1), sigmas)
    plt.ylim(min([min(d) for d in no_error_data]) * 0.85,
             max([max(d) for d in no_error_data]) / 0.85)
    plt.legend(loc=2)

    if for_paper:
        fmt = 'sojourn-vs-error_{}_{}_{}_{}.eps'
        fname = fmt.format(scheduler, dataset, d_over_n, load)
        plt.savefig(fname)

if not for_paper:
    plt.show()

exit()

FIFO_sojourn = avg_sojourn('FIFO', 0)
PS_sojourn = avg_sojourn('PS', 0)
SRPT_sojourn = avg_sojourn('SRPT', 0)

print("FIFO", FIFO_sojourn, "; PS", PS_sojourn, "; SRPT", SRPT_sojourn)

for scheduler in ['SRPT', 'FSP']:
    plt.figure(scheduler)
    plt.xlabel("$\sigma$")
    plt.ylabel('mean sojourn time (s)')
    sigmas = sorted(results[scheduler].keys())[:-1]
    # plt.semilogy([-1, len(sigmas) + 1], [FIFO_sojourn, FIFO_sojourn],
    #              '-.', label='FIFO')
    plt.semilogy([-1, len(sigmas) + 1], [PS_sojourn, PS_sojourn],
                 ':', label='PS')
    plt.semilogy([-1, len(sigmas) + 1], [SRPT_sojourn, SRPT_sojourn],
                 label='SRPT (no error)')
    sojourns = [avg_sojourns(scheduler, sigma) for sigma in sigmas]
    plt.boxplot(sojourns)
    plt.xticks(range(1, len(sigmas) + 1), sigmas)
#    plt.ylim(SRPT_sojourn * 0.85, FIFO_sojourn / 0.85)
    plt.ylim(8, 200)
    plt.legend(loc=2)
    plt.savefig('{}.eps'.format(scheduler))
    
plt.show()



