#!/usr/bin/env python3

import argparse
import collections
import glob
import shelve
import os.path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, LogLocator
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D

names = ['FIFO', 'PS', 'SRPT', 'FSP', 'LAS', 'SRPTE', 'SRPTE+PS', 'SRPTE+LAS',
         'FSPE', 'FSPE+PS', 'FSPE+LAS']
axes = 'shape sigma load timeshape njobs'.split()

parser = argparse.ArgumentParser(description="3d plot of mean sojourn time")
parser.add_argument('scheduler', help="scheduler for which to plot results",
                    choices=names)
parser.add_argument('dirname', help="directory in which results are stored")
parser.add_argument('--xaxis', default='shape', choices=axes,
                    help='what to put in the x-axis; default: shape')
parser.add_argument('--yaxis', default='sigma', choices=axes,
                    help='what to put in the y-axis; default: sigma')
parser.add_argument('--linx', default=False, action='store_true',
                    help='linear (instead of logarithmic) x axis')
parser.add_argument('--liny', default=False, action='store_true',
                    help='linear (instead of logarithmic) y axis')
parser.add_argument('--linz', default=False, action='store_true',
                    help='linear (instead of logarithmic) z axis')
parser.add_argument('--normalize', choices=names,
                    help="normalize against another scheduler")
parser.add_argument('--shape', type=float, default=0.5,
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
args = parser.parse_args()

xaxis_idx = axes.index(args.xaxis)
yaxis_idx = axes.index(args.yaxis)

fname_regex = [str(getattr(args, ax)) for ax in axes]
fname_regex[xaxis_idx] = fname_regex[yaxis_idx] = '[0-9.]*'
glob_str = os.path.join(args.dirname,
                        'res_{}_[0-9.]*.s'.format('_'.join(fname_regex)))
fnames = glob.glob(glob_str)

cache = shelve.open(os.path.join(args.dirname, 'cache.s'))
def getmean(fname, scheduler):
    key = '{}_mean_{}'.format(os.path.split(fname)[1], scheduler)
    try:
        return cache[key]
    except KeyError:
        shelve_ = shelve.open(fname, 'r')
        mean = np.array(shelve_[scheduler]).mean()
        shelve_.close()
        cache[key] = mean
        return mean

results = collections.defaultdict(list)
xvals, yvals = set(), set()
for fname in fnames:
    print('.', end='', flush=True)
    split = os.path.splitext(os.path.split(fname)[1])[0].split('_')[1:-1]
    xval = float(split[xaxis_idx])
    if args.xaxis == 'load':
        xval = 1 - xval
    yval = float(split[yaxis_idx])
    if args.yaxis == 'load':
        yval = 1 - yval
    xvals.add(xval)
    yvals.add(yval)
    try:
        mst = getmean(fname, args.scheduler)
        if args.normalize:
            mst = mst / getmean(fname, args.normalize)
    except:
        # the file is being written now
        continue
    results[xval, yval].append(mst)
cache.close()

print()
xvals = sorted(xvals)
yvals = sorted(yvals)
X, Y = np.meshgrid(xvals, yvals)
if not args.linx:
    X = np.log2(X)
if not args.liny:
    Y = np.log2(Y)
Z = np.zeros_like(X)

for i, xval in enumerate(xvals):
    for j, yval in enumerate(yvals):
        z = np.array(results[xval, yval]).mean()
        Z[j, i] = z if args.linz else np.log2(z)

def format_func(x, pos):
    return '{:.3g}'.format(2 ** x)
formatter = FuncFormatter(format_func)

def load_format(x, pos):
    return '{:.3g}'.format(1 - 2 ** x)
load_formatter = FuncFormatter(load_format)
def load_linformat(x, pos):
    return str(1 - x)
load_linformatter = FuncFormatter(load_linformat)
        
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.set_xlabel(args.xaxis)
ax.set_ylabel(args.yaxis)
if args.xaxis == 'load':
    if args.linx:
        ax.xaxis.set_major_formatter(load_linformatter)
    else:
        ax.xaxis.set_major_formatter(load_formatter)
elif not args.linx:
    ax.xaxis.set_major_formatter(formatter)
if args.yaxis == 'load':
    if args.linx:
        ax.yaxis.set_major_formatter(load_linformatter)
    else:
        ax.yaxis.set_major_formatter(load_formatter)
elif not args.linx:
    ax.yaxis.set_major_formatter(formatter)
if args.normalize:
    zlabel = "MST / MST({})".format(args.normalize)
else:
    zlabel = "Mean sojourn time"
ax.set_zlabel(zlabel)
if not args.linz:
    ax.zaxis.set_major_formatter(formatter)
plt.title(args.scheduler)
if args.normalize:
    if args.linz:
        surf = ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.Greens,
                               linewidth=0.05)
    else:
        surf = ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.bwr,
                               linewidth=0.05, vmin=-6, vmax=6)
else:
    surf = ax.plot_surface(X, Y, Z, rstride=1, cstride=1,
                           linewidth=0.05, cmap=cm.Greens)
plt.show()
