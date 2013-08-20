#!/usr/bin/env python3

from __future__ import division, print_function

import argparse
import collections

SwimJob = collections.namedtuple('SwimJob', 'jobid t delta m s r')
Job = collections.namedtuple('Job', 'jobid t size')

def parse_swim(fname, d_over_n, load):

    jobs = []
    
    for line in open(fname):
        values = line.strip().split('\t')
        values[1:] = map(int, values[1:])
        values = SwimJob(*values)
        jobs.append(Job(values.jobid, values.t,
                        values.m + (1 + d_over_n) * values.s + values.r))

    duration = jobs[-1].t
    multiplier = load * duration / sum(j.size for j in jobs)

    return [(j.jobid, j.t, j.size * multiplier) for j in jobs]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Output a job submission "
                                     "schedule based on a SWIM .tsv workload")
    parser.add_argument('tsv_file', help="SWIM .tsv file")
    parser.add_argument('--d_over_n', type=float, help="d over n parameter "
                        "representing the aggregate speed of disks over "
                        "network in the simulated cluster (default 4)",
                        default=4)
    parser.add_argument('--load', type=float, help="load (default 0.9). "
                        "Consult our technical report for details",
                        default=0.9)
    args = parser.parse_args()

    fmt = "{}\t{}\t{}"
    for jobid, t, size in parse_swim(args.tsv_file, args.d_over_n, args.load):
        print(fmt.format(jobid, t, size))
