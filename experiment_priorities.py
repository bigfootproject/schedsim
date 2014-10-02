#!/usr/bin/env python3

from __future__ import print_function

import argparse
import numpy
import os.path
import random
import shelve
import sys

import weibull_workload
import simulator
import schedulers

parser = argparse.ArgumentParser(description="Experiment on synthetic "
                                 "workloads when jobs have priorities; "
                                 "results will be stored in "
                                 "DIRNAME/pri_SHAPE_SIGMA_LOAD_TIMESHAPE_NJOBS_SEED.s"
                                 )
parser.add_argument('dirname', help="directory in which to store results")
parser.add_argument('--shape', type=float, default=0.25,
                    help="shape parameter for the distribution of job size; "
                    "the scale parameter is set to ensure mean=1; "
                    "default is 0.25")
parser.add_argument('--sigma', type=float, default=0.5,
                    help="sigma parameter for the log-normal error function; "
                    "default is 0.5")
parser.add_argument('--load', type=float, default=0.9,
                    help="average load; default is 0.9")
parser.add_argument('--timeshape', type=float, default=1,
                    help="shape parameter for the Weibull distribution of "
                    "inter-arrival time; default is 1 (i.e., exponential "
                    "distribution)")
parser.add_argument('--njobs', type=int, default=10000,
                    help="number of jobs in the synthetic workload; default "
                    "is 10000")
parser.add_argument('--iterations', type=int, default=1,
                    help="number of times the experiment is run per "
                    "synthetic workload generated; default is 1")
parser.add_argument('--est_factor', type=float, default=1.0,
                    help="multiply estimated size by this value")
parser.add_argument('--normal_error', default=False, action='store_true',
                    help="error function distributed according to a normal "
                    "rather than a log-normal")
parser.add_argument('--alpha', type=float, default=1.0,
                    help="priority class x gets a weight of x**(-alpha); "
                    "default is 1")
parser.add_argument('--seed', type=int, help="random seed")

args = parser.parse_args()

if args.seed is None:
    seed = random.randrange(2 ** 32)
else:
    seed = args.seed

random.seed(seed)

jobs, priorities = weibull_workload.workload_priorities(
    args.shape, args.load, args.njobs, args.timeshape, seed)
jobs = [(i, t, size) for i, (t, size) in enumerate(jobs)]
weights = [p ** (-args.alpha) for p in priorities]

errfunc = (simulator.normal_error if args.normal_error
           else simulator.lognorm_error)
if args.est_factor:
    error = errfunc(args.sigma, args.est_factor)
else:
    error = errfunc(args.sigma)
    

instances = [
    ('WFQE+GPS', schedulers.WFQE_GPS, error, args.iterations),
    ('GPS', schedulers.GPS, error, args.iterations),
    ]

job_start = {jobid: t for (jobid, t, _) in jobs}

basename = 'pri_normal' if args.normal_error else 'pri'

fname_mask = '{}_{}_{}_{}_{}_{}_{}_{}_{}.s'
fname = fname_mask.format(basename, args.shape, args.sigma, args.load,
                          args.timeshape, args.njobs, args.est_factor,
                          args.alpha, seed)
final_results = shelve.open(os.path.join(args.dirname, fname))

for name, scheduler, errfunc, args.iterations in instances:

    print(name, end='')

    sojourns_per_priority = {pri: [] for pri in range(1, 6)}
    
    if args.iterations is None:
        # if no. of iterations is None, it means that a single pass is
        # enough (no randomness there)
        if name in final_results:
            continue
        else:
            args.iterations = 1

    scheduler_results = final_results.get(name, [])

    for i in range(args.iterations - len(scheduler_results)):
        results = list(simulator.simulator(jobs, scheduler, errfunc,
                                           weights))
        sojourns = numpy.zeros(args.njobs)
        for compl, jobid in results:
            sojourn = compl - job_start[jobid]
            sojourns[jobid] = sojourn
            sojourns_per_priority[priorities[jobid]].append(sojourn)
        scheduler_results.append(sojourns)
        print('', sojourns.mean(), end='')
        sys.stdout.flush()
    final_results[name] = scheduler_results
    print({pri: numpy.array(s).mean()
           for pri, s in sojourns_per_priority.items()})
    print()

final_results.close()
