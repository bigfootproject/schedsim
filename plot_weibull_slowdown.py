#!/usr/bin/env python3

from __future__ import division

import argparse
import collections
import glob
import shelve
import os.path

import numpy as np
import matplotlib.pyplot as plt

import plot_helpers
import weibull_workload

axes = 'shape sigma load timeshape njobs'.split()

parser = argparse.ArgumentParser(description="plot CDF of slowdown")
parser.add_argument('dirname', help="directory in which results are stored")
parser.add_argument('--shape', type=float, default=0.25,
                    help="shape for job size distribution; default: 0.25")
parser.add_argument('--sigma', type=float, default=0.5,
                    help="sigma for size estimation error log-normal "
                    "distribution; default: 0.5")
parser.add_argument('--load', type=float, default=0.9,
                    help="load for the generated workload; default: 0.9")
parser.add_argument('--timeshape', type=float, default=1,
                    help="shape for the Weibull distribution of job "
                    "inter-arrival times; default: 1 (i.e. exponential)")
parser.add_argument('--njobs', type=int, default=10000,
                    help="number of jobs in the workload; default: 10000")
parser.add_argument('--nolatex', default=False, action='store_true',
                    help="disable LaTeX rendering")
parser.add_argument('--xmin', type=float, default=1,
                    help="minimum value on the x axis")
parser.add_argument('--xmax', type=float,
                    help="maximum value on the x axis")
parser.add_argument('--ymin', type=float, default=0,
                    help="minimum value on the y axis")
parser.add_argument('--ymax', type=float, default=1,
                    help="maximum value on the y axis")
parser.add_argument('--nolegend', default=False, action='store_true',
                    help="don't put a legend in the plot")
parser.add_argument('--legend_loc', default=0,
                    help="location for the legend (see matplotlib doc)")
parser.add_argument('--normal_error', default=False, action='store_true',
                    help="error function distributed according to a normal "
                    "rather than a log-normal")
parser.add_argument('--alt_schedulers', default=False, action='store_true',
                     help="plot schedulers that are variants of FSPE+PS")
parser.add_argument('--save', help="don't show but save in target filename")
args = parser.parse_args()

if args.alt_schedulers:
    plotted = 'FSPE+PS FSPE+LAS SRPTE+PS SRPTE+LAS'.split()
    styles = {'FSPE+PS': '-', 'FSPE+LAS': '--',
              'SRPTE+PS': ':', 'SRPTE+LAS': '-.'}
    colors = {'FSPE+PS': 'r', 'FSPE+LAS': 'r',
              'SRPTE+PS': 'r', 'SRPTE+LAS': 'r'}
else:
    plotted = 'SRPTE FSPE FSPE+PS PS LAS FIFO'.split()
    styles = {'FIFO': ':', 'PS': '-', 'LAS': '--',
              'SRPTE': '--', 'FSPE': ':', 'FSPE+PS': '-'}
    colors = {'FIFO': '0.6', 'PS': '0.6', 'LAS': '0.6',
              'SRPTE': 'r', 'FSPE': 'r', 'FSPE+PS': 'r'}        



fname_regex = [str(getattr(args, ax)) for ax in axes]
head = 'normal' if args.normal_error else 'res'
glob_str = os.path.join(args.dirname,
                        '{}_{}_[0-9.]*.s'.format(head, '_'.join(fname_regex)))
fnames = glob.glob(glob_str)

def sizes(seed):
    gen = weibull_workload.workload(args.shape, args.load, args.njobs,
                                    args.timeshape, seed)
    return [size for _, size in gen]

results = collections.defaultdict(list)
for fname in fnames:
    print('.', end='', flush=True)
    seed = int(os.path.splitext(fname)[0].split('_')[-1])
    job_sizes = sizes(seed)
    try:
        shelve_ = shelve.open(fname, 'r')
    except:
        # the file is being written now
        continue
    else:
        for scheduler in plotted:
            for sojourns in shelve_[scheduler]:
                slowdowns = (sojourn / size
                             for sojourn, size in zip(sojourns, job_sizes))
                results[scheduler].extend(slowdowns)

print()

fig = plt.figure(figsize=(8, 4.5))
ax = fig.add_subplot(111)
ax.set_xlabel("slowdown")
ax.set_ylabel("ECDF")
ys = np.linspace(max(0, args.ymin), min(1, args.ymax), 100)
for scheduler in plotted:
    slowdowns = results[scheduler]
    slowdowns.sort()
    last_idx = len(slowdowns) - 1
    indexes = np.linspace(max(0, args.ymin) * last_idx,
                          min(1, args.ymax) * last_idx,
                          100).astype(int)
    xs = [slowdowns[idx] for idx in indexes]
    style = styles[scheduler]
    ax.semilogx(xs, ys, style, label=scheduler, linewidth=4,
                color=colors[scheduler])

if not args.nolegend:
    ax.legend(loc=args.legend_loc, ncol=2)
    
ax.tick_params(axis='x', pad=7)

ax.set_xlim(left=args.xmin)
if args.xmax is not None:
    ax.set_xlim(right=args.xmax)
ax.set_ylim(args.ymin, args.ymax)

if not args.nolatex:
    plot_helpers.config_paper(20)

plt.tight_layout(1)
plt.grid()

if args.save is not None:
    plt.savefig(args.save)
else:
    plt.show()
