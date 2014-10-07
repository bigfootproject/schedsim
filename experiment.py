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
parser.add_argument('file', help="file with the trace to use")
parser.add_argument('iterations', type=int,
                    help="Iterations for each run of the experiment. "
                    "If that number of iterations is already in the "
                    "results file, nothing will be done.")
parser.add_argument('--read_estimations', default=False, action='store_true',
                    help="Read job size estimations from the input file. "
                    "Ignored if --parse_swim is set")
parser.add_argument('--sigma', type=float, default=0.5,
                    help="sigma parameter for the log-normal error function; "
                    "default: 0.5. Ignored if --read_estimations is set.")
parser.add_argument('--parse_swim', dest='parse_swim', default=False,
                    action='store_true',
                    help="parse data from a SWIM .tsv file")
parser.add_argument('-dn', '--d-over-n', dest="d_over_n", type=float,
                    default=4.0, help="ratio between disk and network "
                    "bandwidth in the simulated cluster; default is 4. "
                    "Ignored unless --parse-swim is set")
parser.add_argument('--load', type=float, default=0.9,
                    help="average load in the simulated cluster; default is "
                    "0.9. "
                    "Ignored unless --parse-swim is set")
parser.add_argument('--nojobid', default=False, action='store_true',
                    help="input files do not have jobids")
args = parser.parse_args()

if args.parse_swim:
    jobs = parse_swim(args.file, args.d_over_n, args.load)
else:
    with open(args.file) as f:
        jobs = (line.strip().split() for line in f)
        if args.read_estimations:
            args.sigma = None
            old_jobs = jobs
            jobs, estimations = [], []
            for job in old_jobs:
                jobs.append(job[:-1])
                estimations.append(float(job[-1]))
        if args.nojobid:
            jobs = ((i, t, size) for i, (t, size) in enumerate(jobs))
        jobs = [(jobid, float(t), float(size)) for jobid, t, size in jobs]

error = (lambda: simulator.fixed_estimations(estimations)
         if args.read_estimations
         else lambda: simulator.lognorm_error(args.sigma))

instances = [
    ('FIFO', schedulers.FIFO, simulator.identity, None),
    ('PS', schedulers.PS, simulator.identity, None),
    ('SRPT (no error)', schedulers.SRPT, simulator.identity, None),
    ('FSP (no error)', schedulers.FSP, simulator.identity, None),
    ('LAS', schedulers.LAS, simulator.identity, None),
    ('SRPT', schedulers.SRPT, error(), args.iterations),
    ('SRPT + PS', schedulers.SRPT_plus_PS, error(), args.iterations),
    ('FSP + FIFO', schedulers.FSP, error(), args.iterations),
    ('FSP + PS', schedulers.FSP_plus_PS, error(), args.iterations),
    ('FSP + LAS', schedulers.FSP_plus_LAS, error(), args.iterations),
    ('SRPT + LAS', schedulers.SRPT_plus_LAS, error(), args.iterations),
    ]

jobids = [j[0] for j in jobs]
job_idxs = {jobid: i for i, jobid in enumerate(jobids)}
n_jobs = len(jobids)

job_start = {jobid: start for jobid, start, size in jobs}

if args.parse_swim:
    fname_short = (args.file[:-4] if args.file.endswith('.tsv')
                   else args.file)
    result_fname = 'results_{}_{}_{}_{}.s'
    result_fname = result_fname.format(fname_short, args.sigma, args.d_over_n,
                                       args.load)
else:
    fname_short = (args.file[:-4] if args.file.endswith('.txt')
                   else args.file)
    result_fname = 'results_{}_{}.s'.format(fname_short, args.sigma)
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
