#!/usr/bin/env python3

from __future__ import division

import argparse
import collections
import glob
import itertools
import shelve
import os.path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, ScalarFormatter, AutoLocator

import weibull_workload

names = ['WFQE+GPS', 'GPS']

plotted = 'WFQE+GPS GPS'.split()

styles = itertools.cycle('- -- :'.split())
markers = {'WFQE+GPS': 'x', 'GPS': '+'}
colors = {'WFQE+GPS': 'r', 'GPS': '0.6'}

parser = argparse.ArgumentParser(description="plot of mean sojourn time vs. "
                                             "priorities")
parser.add_argument('dirname', help="directory in which results are stored")
parser.add_argument('--shape', type=float, default=0.25,
                    help="shape for job size distribution "
                    "(if not on one of the axes); default: 0.5")
parser.add_argument('--sigma', type=float, default=0.5,
                    help="sigma for size estimation error log-normal "
                    "distribution (if not on one of the axes); default: 0.5")
parser.add_argument('--load', type=float, default=0.9,
                    help="load for the generated workload; default: 0.99")
parser.add_argument('--timeshape', type=float, default=1,
                    help="shape for the Weibull distribution of job "
                    "inter-arrival times; default: 1 (i.e. exponential)")
parser.add_argument('--njobs', type=int, default=10000,
                    help="number of jobs in the workload; default: 10000")
parser.add_argument('--est_factor', type=float, default=1.0,
                    help="multiply estimated size by this value")
parser.add_argument('--nolatex', default=False, action='store_true',
                    help="disable LaTeX rendering")
parser.add_argument('--xmin', type=float, default=0.95,
                    help="minimum value on the x axis")
parser.add_argument('--xmax', type=float, default=5.05,
                    help="maximum value on the x axis")
parser.add_argument('--ymin', type=float, default=1,
                    help="minimum value on the y axis")
parser.add_argument('--ymax', type=float,
                    help="maximum value on the y axis")
parser.add_argument('--nolegend', default=False, action='store_true',
                    help="don't put a legend in the plot")
parser.add_argument('--normal_error', default=False, action='store_true',
                    help="error function distributed according to a normal "
                    "rather than a log-normal")
parser.add_argument('--save', help="don't show but save in target filename")
args = parser.parse_args()

fname_regex = '_'.join(str(getattr(args, param))
                       for param in
                       'shape sigma load timeshape njobs est_factor'.split())
head = 'pri_normal' if args.normal_error else 'pri'
glob_str = os.path.join(args.dirname,
                        '{}_{}_[0-9.]*_[0-9.]*.s'.format(head, fname_regex))
fnames = glob.glob(glob_str)

def get_basename(fname):
    return os.path.splitext(os.path.split(fname)[1])[0]

cache = shelve.open(os.path.join(args.dirname, 'pri_cache.s'))
def getmeans(fname, scheduler):
    basename = get_basename(fname)
    key = '{}_mean_{}'.format(basename, scheduler)
    try:
        return cache[key]
    except KeyError:
        shelve_ = shelve.open(fname, 'r')
        seed = int(basename.split('_')[-1])
        _, priorities = weibull_workload.workload_priorities(
            args.shape, args.load, args.njobs, args.timeshape, seed)
        sojourns = collections.defaultdict(list)
        for results in shelve_.get(scheduler, []):
            for sojourn, pri in zip(results, priorities):
                sojourns[pri].append(sojourn)
        means = {pri: np.array(s).mean() for pri, s in sojourns.items()}
        shelve_.close()
        cache[key] = means
        return means

# results[alpha][scheduler][priority] = list of MSTs per experiment
results = collections.defaultdict(lambda:
              collections.defaultdict(lambda:
                  collections.defaultdict(list)))
for fname in fnames:
    print('.', end='', flush=True)
    for scheduler in plotted:
        alpha = float(get_basename(fname).split('_')[-2])
#        try:
        means = getmeans(fname, scheduler)
#        except:
            # the file is being written now
#            continue
        for pri, mst in means.items():
            results[alpha][scheduler][pri].append(mst)
cache.close()

print()

fig = plt.figure(figsize=(8, 4.5))
ax = fig.add_subplot(111)
ax.set_xlabel("Priority")
ax.set_ylabel("Mean sojourn time")
for alpha, alpha_results in sorted(results.items()):
    style = next(styles)
    for scheduler in plotted:
        sched_results = sorted(alpha_results[scheduler].items())
        xs, ys = zip(*[(x, sum(ys) / len(ys)) for x, ys in sched_results])
        label = r"{}, $\alpha={}$".format(scheduler, alpha)
        ax.plot(xs, ys, style + markers[scheduler],
                label=label, linewidth=2, markersize=10,
                color=colors[scheduler])

if not args.nolegend:
    ax.legend(loc=0, ncol=2)
    
ax.tick_params(axis='x', pad=7)

ax.yaxis.set_major_formatter(ScalarFormatter())
ax.set_xlim(left=args.xmin)
ax.set_xlim(right=args.xmax)
ax.set_ylim(bottom=args.ymin)
if args.ymax is not None:
    ax.set_ylim(top=args.ymax)

if not args.nolatex:
    import plot_helpers
    plot_helpers.config_paper(20)

ax.grid()
plt.tight_layout(1)

if args.save is not None:
    plt.savefig(args.save)
else:
    plt.show()
