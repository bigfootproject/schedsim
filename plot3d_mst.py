#!/usr/bin/env python3

import argparse
import glob
import shelve
import os.path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, LogLocator
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D

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

epilog_string = "Available schedulers: {}.".format(', '.join(sorted(old_names)))

parser = argparse.ArgumentParser(description="3d plot: mean sojourn time "
                                 "varying error and shape of job size",
                                 epilog=epilog_string)
parser.add_argument('scheduler', help="scheduler for which to plot results")
parser.add_argument('--normalize', help="normalize against another scheduler")
parser.add_argument('--load', type=float, default=0.99,
                    help="load for the generated workload; default is "
                    "0.99")
parser.add_argument('--fix_sigma', type=float, help="Vary load on the y axis "
                    "rather than sigma, fix sigma to this value.")
args = parser.parse_args()

if args.fix_sigma:
    glob_str = 'results_weibull_[0-9.]*_[0-9.]*_{}.s'.format(args.fix_sigma)
else:
    glob_str = 'results_weibull_[0-9.]*_{}_[0-9.]*.s'.format(args.load)
fnames = glob.glob(glob_str)
results = {}
shapes, sigmas = set(), set()
for fname in fnames:
    split = os.path.splitext(fname)[0].split('_')
    shape = float(split[2])
    if args.fix_sigma:
        # quick and dirty: we put (1 - load) here in the place of sigma
        sigma = 1 - float(split[3])
    else:
        sigma = float(split[4])
    shelve_ = shelve.open(fname, 'r')
    mst = np.array(shelve_[old_names[args.scheduler]]).mean()
    if args.normalize:
        mst = mst / np.array(shelve_[old_names[args.normalize]]).mean()
    results[shape, sigma] = mst
    shapes.add(shape)
    sigmas.add(sigma)

shapes = sorted(shapes)
sigmas = sorted(sigmas)
X, Y = np.log2(np.meshgrid(shapes, sigmas))
Z = np.zeros_like(X)

for i, shape in enumerate(shapes):
    for j, sigma in enumerate(sigmas):
        Z[j, i] = np.log2(results[shape, sigma])

def format_func(x, pos):
    return '{:.3g}'.format(2 ** x)
        
formatter = FuncFormatter(format_func)
        
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.set_xlabel('Shape')
ax.xaxis.set_major_formatter(formatter)
if args.fix_sigma:
    ax.set_ylabel('Load')
    def load_format(x, pos):
        return '{:.3g}'.format(1 - 2 ** x)
    ax.yaxis.set_major_formatter(FuncFormatter(load_format))
else:
    ax.set_ylabel('Sigma')
    ax.yaxis.set_major_formatter(formatter)
if args.normalize:
    zlabel = "MST / MST({})".format(args.normalize)
else:
    zlabel = "Mean sojourn time"
ax.set_zlabel(zlabel)
ax.zaxis.set_major_formatter(formatter)
plt.title(args.scheduler)
if args.normalize:
    surf = ax.plot_surface(X, Y, Z, rstride=1, cstride=1,
                           cmap=cm.bwr, linewidth=0.05, vmin=-6, vmax=6)
else:
    surf = ax.plot_surface(X, Y, Z, rstride=1, cstride=1,
                           linewidth=0.05, cmap=cm.Greens)
plt.show()
