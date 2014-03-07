#!/usr/bin/env python3

from __future__ import print_function

import argparse
import itertools
import os.path
import random
import shelve
import sys

import numpy
import scipy.stats

import norta
import simulator
import schedulers

parser = argparse.ArgumentParser(description="Run our experiment replicating "
                                 "settings by Lu et al., MASCOTS 2004; "
                                 "results will be stored in "
                                 "DIRNAME/lu_SHAPE_CORR_LOAD_TIMESHAPE_NJOBS_ESTFACTOR_SEED.s"
                                 )
parser.add_argument('dirname', help="directory in which to store results")
parser.add_argument('--shape', type=float, default=2,
                    help="shape parameter for the Pareto distribution of "
                    "job size; default is 2")
parser.add_argument('--loc', type=float, default=-1,
                    help="loc parameter for the distribution of job size; "
                    "default is -1")
parser.add_argument('--corr', type=float, default=0.5,
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
parser.add_argument('--est_factor', type=float, default=1,
                    help="multiply estimated size by this value")
parser.add_argument('--seed', type=int, help="random seed")
args = parser.parse_args()

if args.seed is None:
    seed = random.randrange(2 ** 32)
else:
    seed = args.seed

random.seed(seed)

sizes, estimations = norta.generate(args.corr, args.njobs,
                                    scipy.stats.pareto(args.shape, args.loc))
times = numpy.cumsum(scipy.stats.weibull_min(args.timeshape).rvs(args.njobs))
times *= sizes.sum() * args.load / times[-1]

jobs = [(i, t, s) for i, (t, s) in enumerate(zip(times, sizes))]

est_iter = itertools.cycle(estimations)
def error(_):
    return args.est_factor * next(est_iter)
                    
instances = [
    ('FIFO', schedulers.FIFO, simulator.identity, None),
    ('PS', schedulers.PS, simulator.identity, None),
    ('SRPT', schedulers.SRPT, simulator.identity, None),
    ('FSP', schedulers.FSP, simulator.identity, None),
    ('LAS', schedulers.LAS, simulator.identity, None),
    ('SRPTE', schedulers.SRPT, error, args.iterations),
#    ('SRPTE+PS', schedulers.SRPT_plus_PS, error, args.iterations),
#    ('SRPTE+LAS', schedulers.SRPT_plus_LAS, error, args.iterations),
    ('FSPE', schedulers.FSP, error, args.iterations),
    ('FSPE+PS', schedulers.FSP_plus_PS, error, args.iterations),
#    ('FSPE+LAS', schedulers.FSP_plus_LAS, error, args.iterations),
    ]

jobids = [jobid for jobid, _, _ in jobs]
job_idxs = {jobid: i for i, jobid in enumerate(jobids)}
n_jobs = len(jobids)

job_start = {jobid: start for jobid, start, size in jobs}

fname_mask = 'lu_{}_{}_{}_{}_{}_{}_{}_{}.s'
fname = fname_mask.format(args.shape, args.loc, args.corr, args.load,
                          args.timeshape, args.njobs, args.est_factor,
                          seed)
final_results = shelve.open(os.path.join(args.dirname, fname))

for name, scheduler, errfunc, args.iterations in instances:

    print(name, end='')

    if args.iterations is None:
        # if no. of iterations is None, it means that a single pass is
        # enough (no randomness there)
        if name in final_results:
            continue
        else:
            args.iterations = 1

    scheduler_results = final_results.get(name, [])

    for i in range(args.iterations - len(scheduler_results)):
        results = list(simulator.simulator(jobs, scheduler, errfunc))
        sojourns = numpy.zeros(n_jobs)
        for compl, jobid in results:
            sojourns[job_idxs[jobid]] = compl - job_start[jobid]
        scheduler_results.append(sojourns)
        print('', sojourns.mean(), end='')
        sys.stdout.flush()
    print()

    final_results[name] = scheduler_results

final_results.close()
