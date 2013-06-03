from __future__ import division

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
