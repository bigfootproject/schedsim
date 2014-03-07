# Based on Lu et al.'s model for generating distributions with
# arbitrary coefficients

import math

import numpy
import scipy.stats

normal = scipy.stats.norm()

def generate(r, n, real_dist=normal, est_dist=None, eps=0.01):
    rho = r
    if est_dist is None:
        est_dist = real_dist
    low, high = 0, 1
    while True:
        y1, x2 = normal.rvs((2, n))
        y2 = rho * y1 +  (1 - rho ** 2) ** 0.5 * x2
        u1, u2 = normal.cdf([y1, y2])
        est = est_dist.ppf(u1)
        real = real_dist.ppf(u2)
        diff = r - numpy.corrcoef(est, real)[0, 1]
        if diff < -eps:
            high = rho
        elif diff < eps:
            return est, real
        else:
            low = rho
        rho = (low + high) / 2
