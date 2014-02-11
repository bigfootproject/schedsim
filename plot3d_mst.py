#!/usr/bin/env python3

import shelve

from glob import glob

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

parser = argparse.ArgumentParser(description="3d plot: mean sojourn time "
                                 "varying error and shape of job size")
parser.add_argument('scheduler', help="scheduler for which to plot results")
parser.add_argument('--load', type=float, default=0.99,
                    help="load for the generated workload; default is "
                    "0.99")
args = parser.parse_args()

glob_str = 'results_weibull_[0-9.]*_{}_[0-9.]*.s'.format(args.load)
fnames = glob(glob_str)
shapes, sigmas, mst = [], [], []
shelves = {}
for fname in fnames:
    split = fname.split('_')
    shapes.append(float(split[2]))
    sigmas.append(float(split[4]))
    mst.append(np.array(shelve.open(fname, 'r')[scheduler]).mean())

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

ax.plot_surface(shapes, sigmas, mst)
