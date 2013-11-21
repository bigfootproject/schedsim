#!/usr/bin/env python3

from __future__ import print_function

import sys
import argparse

import schedulers
import simulator

parser = argparse.ArgumentParser(description="Comparative experiment between "
                                 "schedulers. Print results on standard "
                                 "output.")
parser.add_argument('schedule', help="file with submission schedule: "
                    "each line is a whitespace-separated (id, t, d) triple "
                    "where id is a job-id, t is the submission time and d "
                    "is the job duration")
parser.add_argument('--sigma', type=float, default=1,
                    help="sigma parameter for the log-normal error function "
                    "(default 1)")
parser.add_argument('--estimations', help="file with estimations: "
                    "each line is a whitespace-separated (id, e) pair "
                    "where id is a job-id and e is its estimation. Overrides "
                    "errors that would be computed otherwise")
args = parser.parse_args()

with open(args.schedule) as f:
    jobs = []
    for line in f:
        jobid, t, d = line.strip().split()
        jobs.append([jobid, float(t), float(d)])

preset_est = {}
if args.estimations is not None:
    with open(args.estimations) as f:
        for line in f:
            jobid, e = line.strip().split()
            preset_est[jobid] = float(e)
            
estimations = []
err_func = simulator.lognorm_error(args.sigma)            
for jobid, _, d in jobs:
    estimations.append(preset_est.get(jobid, err_func(d)))

instances = [#('FIFO', schedulers.FIFO),
             #('PS', schedulers.PS),
             #('SRPT', schedulers.SRPT),
             #('SRPTPS', schedulers.SRPT_plus_PS),
             #('FSP', schedulers.FSP),
             #('FSP+PS', schedulers.FSP_plus_PS),
             ('LAS', schedulers.LAS),
             ('LAS2', schedulers.LAS2),
             #('FSP+LAS', schedulers.FSP_plus_LAS),
            ]

results = {}
for name, scheduler in instances:
    sim = simulator.simulator(jobs, scheduler,
                              simulator.fixed_estimations(estimations))
    results[name] = {jobid: t for t, jobid in sim}


head_fmt = '\t'.join(['{}'] * (len(instances) + 4))
fmt = '\t'.join(['{}'] + ['{:.2f}'] * (len(instances) + 3))

scheduler_names = [n for n, _ in instances]
header = head_fmt.format('Job', 'Arr.', 'Size', 'Est.', *scheduler_names)
print(header)
print('=' * len(header.expandtabs()))
for (jobid, arrival, d), e in zip(jobs, estimations):
    print(fmt.format(jobid, arrival, d, e,
                     *(results[n][jobid] for n in scheduler_names)))
    
    
