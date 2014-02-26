#!/usr/bin/env python3

from __future__ import division

import argparse
import collections
import glob
import shelve
import os.path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, ScalarFormatter, AutoLocator

old_names = {'FIFO': 'FIFO',
             'PS': 'PS',
             'SRPT': 'SRPT (no error)',
             'FSP': 'FSP (no error)',
             'LAS': 'LAS',
             'SRPTE': 'SRPT',
             'SRPTE+PS': 'SRPT + PS',
             'SRPTE+LAS': 'SRPT + LAS',
             'FSPE': 'FSP + FIFO',
             'FSPE+PS': 'FSP + PS',
             'FSPE+LAS': 'FSP + LAS'}

names = ['FIFO', 'PS', 'SRPT', 'FSP', 'LAS', 'SRPTE', 'SRPTE+PS', 'SRPTE+LAS',
         'FSPE', 'FSPE+PS', 'FSPE+LAS']

plotted = 'SRPTE FSPE FSPE+PS PS LAS FIFO'.split()

styles = {'FIFO': ':+', 'PS': '-+', 'LAS': '--+',
          'SRPTE': '--x', 'FSPE': ':x', 'FSPE+PS': '-x'}

colors = {'FIFO': '0.6', 'PS': '0.6', 'LAS': '0.6',
          'SRPTE': 'r', 'FSPE': 'r', 'FSPE+PS': 'r'}        

parser = argparse.ArgumentParser(description="plot of mean sojourn time")
parser.add_argument('dataset', help="dataset")
parser.add_argument('--tsv', default=False, action='store_true',
                    help="based on a .tsv file")
parser.add_argument('-dn', '--d-over-n', dest="d_over_n", type=float,
                    default=4.0, help="ratio between disk and network "
                    "bandwidth in the simulated cluster; default is 4. "
                    "Ignored if --tsv is not set.")
parser.add_argument('--load', type=float, default=0.9,
                    help="average load in the simulated cluster; default is "
                    "0.9. Ignored if --tsv is not set.")
parser.add_argument('--linx', default=False, action='store_true',
                    help='linear (instead of logarithmic) x axis')
parser.add_argument('--liny', default=False, action='store_true',
                    help='linear (instead of logarithmic) y axis')
parser.add_argument('--normalize', choices=names,
                    help="normalize against another scheduler")
parser.add_argument('--nolatex', default=False, action='store_true',
                    help="disable LaTeX rendering")
parser.add_argument('--xmin', type=float,
                    help="minimum value on the x axis")
parser.add_argument('--xmax', type=float,
                    help="maximum value on the x axis")
parser.add_argument('--ymin', type=float,
                    help="minimum value on the y axis")
parser.add_argument('--ymax', type=float,
                    help="maximum value on the y axis")
parser.add_argument('--nolegend', default=False, action='store_true',
                    help="don't put a legend in the plot")
parser.add_argument('--nofifo', default=False, action='store_true',
                    help="don't plot FIFO")
parser.add_argument('--save', help="don't show but save in target filename")
args = parser.parse_args()

if args.nofifo:
    plotted.remove('FIFO')

if args.tsv:
    glob_fmt = 'results_{}_[0-9.]*_{}_{}.s'
    glob_str = glob_fmt.format(args.dataset,  args.d_over_n, args.load)
    shelve_files = sorted((float(fname.split('_')[2]), fname)
                          for fname in glob.glob(glob_str))
else:
    glob_fmt = 'results_{}_[0-9.]*.s'
    glob_str = glob_fmt.format(args.dataset)
    shelve_files = sorted((float(fname[:-2].split('_')[-1]), fname)
                          for fname in glob(glob_str))
sigmas = [sigma for sigma, _ in shelve_files]

def getmean(shelve_, scheduler):
    return np.array(shelve_[scheduler]).mean()

results = collections.defaultdict(dict)
for sigma, fname in shelve_files:
    print('.', end='', flush=True)
    try:
        shelve_ = shelve.open(fname, 'r')
    except:
        # the file is being written now
        continue
    for scheduler in plotted:
        mst = getmean(shelve_, old_names[scheduler])
        if args.normalize:
            mst /= getmean(shelve_, old_names[args.normalize])
        results[scheduler][sigma] = mst
    shelve_.close()

print()

fig = plt.figure(figsize=(8, 4.5))
ax = fig.add_subplot(111)
ax.set_xlabel('sigma')
if args.normalize:
    ylabel = "MST / MST({})".format(args.normalize)
else:
    ylabel = "Mean sojourn time"
ax.set_ylabel(ylabel)
for scheduler in plotted:
    sched_results = sorted(results[scheduler].items())
    xs, ys = zip(*sorted(results[scheduler].items()))
    style = styles[scheduler]
    if args.linx:
        if args.liny:
            plotfun = ax.plot
        else:
            plotfun = ax.semilogy
    else:
        if args.liny:
            plotfun = ax.semilogx
        else:
            plotfun = ax.loglog
    plotfun(xs, ys, style, label=scheduler, linewidth=2, markersize=10,
            color=colors[scheduler])

if not args.nolegend:
    ax.legend(loc=0, ncol=2)
    
ax.tick_params(axis='x', pad=7)

ax.xaxis.set_ticks([0.125, 0.25, 0.5, 1, 2, 4])
ax.xaxis.set_ticklabels('0.125 0.25 0.5 1 2 4'.split())
    
ax.yaxis.set_major_formatter(ScalarFormatter())

minvs = min(min(vs) for vs in results.values())
maxvs = max(max(vs) for vs in results.values())

ax.set_xlim(args.xmin if args.xmin is not None else minvs,
            args.xmax if args.xmax is not None else maxvs)

if args.ymin is not None:
    ax.set_ylim(bottom=args.ymin)
if args.ymax is not None:
    ax.set_ylim(top=args.ymax)

if not args.nolatex:
    import plot_helpers
    plot_helpers.config_paper(20)

plt.tight_layout(1)

if args.save is not None:
    plt.savefig(args.save)
else:
    plt.show()
