#!/usr/bin/env python3

from __future__ import print_function

import shelve
import sys

from random import lognormvariate

from numpy import zeros

from swim_parser import parse_swim
import simulator
import schedulers

argv = sys.argv
swim_file, sigma, iterations = argv[1:4]
sigma = float(sigma)
iterations = int(iterations)


if len(argv) >= 5:
    d_over_n = float(argv[4])
else:
    d_over_n = 4

if len(argv) >= 6:
    load = float(argv[5])
else:
    load = 0.9

jobs = parse_swim(swim_file, d_over_n, load)

error = simulator.lognorm_error(sigma)

instances = [
    ('FIFO', schedulers.FIFO, simulator.identity, None),
    ('PS', schedulers.PS, simulator.identity, None),
    ('SRPT (no error)', schedulers.SRPT, simulator.identity, None),
    ('FSP (no error)', schedulers.FSP, simulator.identity, None),
    ('SRPT', schedulers.SRPT, error, iterations),
    ('FSP + FIFO', schedulers.FSP, error, iterations),
    ('FSP + PS', schedulers.FSP_plus_PS, error, iterations),
    ]

jobids = [jobid for jobid, _, _ in jobs]
job_idxs = {jobid: i for i, jobid in enumerate(jobids)}
n_jobs = len(jobids)

job_start = {jobid: start for jobid, start, size in jobs}

fname_short = swim_file[:-4] if swim_file.endswith('tsv') else swim_file    
result_fname = 'results_{}_{}_{}_{}.s'
result_fname = result_fname.format(fname_short, sigma, d_over_n, load)
final_results = shelve.open(result_fname)

for name, scheduler, errfunc, iterations in instances:
    
    print("scheduler:", name)
    
    if iterations is None:
        # if no. of iterations is None, it means that a single pass is
        # enough (no randomness there)
        if name in final_results:
            continue
        else:
            iterations = 1
    elif sigma == 0:
        # No point to compute results for schedulers which don't have error
        continue
    
    scheduler_results = []
    
    for i in range(iterations):
        results = list(simulator.simulator(jobs, scheduler, errfunc))
        sojourns = zeros(n_jobs)
        for compl, jobid in results:
            sojourns[job_idxs[jobid]] = compl - job_start[jobid]
        scheduler_results.append(sojourns)
        print(sojourns.mean(), end=' ')
        sys.stdout.flush()
    print()
    
    res = final_results.get(name, [])
    res.extend(scheduler_results)
    final_results[name] = res
    print()
    
final_results.close()
