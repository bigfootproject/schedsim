#!/usr/bin/env python3

from __future__ import division
from __future__ import print_function

import itertools
import math
import random

def workload_gen(shape, load, time_shape=1, seed=None):

    if seed is not None:
        random.seed(seed)
    
    t = 0
    scale = 1 / math.gamma(1 + 1 / shape)
    time_scale = (1 / math.gamma(1 + 1 / time_shape)) / load
    weibullvariate = random.weibullvariate
    while True:
        yield (t, weibullvariate(scale, shape))
        t += weibullvariate(time_scale, time_shape)

def workload(shape, load, n, time_shape=1, seed=None):
    gen = workload_gen(shape, load, time_shape, seed)
    jobs = list(itertools.islice(gen, n))

    # we now 'stretch' job submission times to ensure the load is
    # exactly the one we wanted
    
    totsize = sum(size for _, size in jobs)
    stretch_factor = totsize / (jobs[-1][0] * load)

    return [(t * stretch_factor, size) for t, size in jobs]
    
        
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate a random workload "
                                    "having Weibull distribution for job size "
                                    "and exponential distribution between "
                                    "arrival time.")
    parser.add_argument('shape', type=float, help="shape parameter for the "
                        "Weibull distribution; the scale is set to have "
                        "mean=1")
    parser.add_argument('load', type=float, help="parameter for the "
                        "exponential arrival time of jobs; results in "
                        "equivalent load")
    parser.add_argument('--seed', type=int, help="random seed")
    parser.add_argument('--interarr', type=float, default=1,
                        help="shape parameter for the Weibull distribution "
                        "of inter-arrival times; default is 1 (i.e. "
                        "exponential distribution)")
    parser.add_argument('n', type=int, help="number of jobs in the workload")
    args = parser.parse_args()

    jobs = workload(args.shape, args.load, args.n, args.interarr, args.seed)
    for jobid, (t, size) in enumerate(jobs):
        print("{}\t{}\t{}".format(jobid, t, size))

if __name__ == '__main__':
    main()
