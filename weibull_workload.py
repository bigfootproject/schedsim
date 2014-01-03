#!/usr/bin/env python3

from __future__ import division
from __future__ import print_function

import itertools
import math
import random

def workload(shape, load, seed=None):

    random.seed(seed)
    
    t = 0
    scale = 1 / math.gamma(1 + 1 / shape)
    weibullvariate = random.weibullvariate
    for i in itertools.count():
        yield (i, t, random.weibullvariate(scale, shape))
        t += random.expovariate(load)

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
    parser.add_argument('n', type=int, help="number of jobs in the workload")
    args = parser.parse_args()

    jobs = itertools.islice(workload(args.shape, args.load, args.seed), args.n)
    for jobid, t, size in jobs:
        print("{}\t{}\t{}".format(jobid, t, size))

if __name__ == '__main__':
    main()
