#!/usr/bin/env python3

from __future__ import print_function

import shelve
import sys

from numpy import zeros

from swim_parser import parse_swim
import simulator
import schedulers

import argparse

parser = argparse.ArgumentParser(description="run the experiment; "
                                 "details on parameters in our TR "
                                 "at http://arxiv.org/abs/1306.6023")
parser.add_argument('swim_file', help=".tsv file with the trace to use")
parser.add_argument('sigma', type=float,
                    help="sigma parameter for the log-normal error function")
parser.add_argument('iterations', type=int,
                    help="Iterations for each run of the experiment. "
                    "If that number of iterations is already in the "
                    "results file, nothing will be done.")
parser.add_argument('-dn', '--d-over-n', dest="d_over_n", type=float,
                    default=4, help="ratio between disk and network "
                    "bandwidth in the simulated cluster; default is 4")
parser.add_argument('--load', type=float, default=0.9,
                    help="average load in the simulated cluster; default is "
                    "0.9")
args = parser.parse_args()

jobs = parse_swim(args.swim_file, args.d_over_n, args.load)

error = simulator.lognorm_error(args.sigma)

instances = [
    ('FIFO', schedulers.FIFO, simulator.identity, None),
    ('PS', schedulers.PS, simulator.identity, None),
    ('SRPT (no error)', schedulers.SRPT, simulator.identity, None),
    ('FSP (no error)', schedulers.FSP, simulator.identity, None),
    ('SRPT', schedulers.SRPT, error, args.iterations),
    ('FSP + FIFO', schedulers.FSP, error, args.iterations),
    ('FSP + PS', schedulers.FSP_plus_PS, error, args.iterations),
    ]

jobids = [jobid for jobid, _, _ in jobs]
job_idxs = {jobid: i for i, jobid in enumerate(jobids)}
n_jobs = len(jobids)

job_start = {jobid: start for jobid, start, size in jobs}

fname_short = (args.swim_file[:-4] if args.swim_file.endswith('tsv')
               else args.swim_file)
result_fname = 'results_{}_{}_{}_{}.s'
result_fname = result_fname.format(fname_short, args.sigma, args.d_over_n,
                                   args.load)
final_results = shelve.open(result_fname)

for name, scheduler, errfunc, args.iterations in instances:
    
    print("scheduler:", name)
    
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
        sojourns = zeros(n_jobs)
        for compl, jobid in results:
            sojourns[job_idxs[jobid]] = compl - job_start[jobid]
        scheduler_results.append(sojourns)
        print(sojourns.mean(), end=' ')
        sys.stdout.flush()
    print()
    
    final_results[name] = scheduler_results
    print()
    
final_results.close()
