from __future__ import division

import random

from heapq import *

import schedulers

ARRIVAL, COMPLETE, INTERNAL = 0, 1, 2
eps = 0.001
rand = random.Random()

def identity(x):
    return x

def lognorm_error(sigma):
    def err_func(x):
        return x * rand.lognormvariate(0, sigma)
    return err_func

def normal_error(sigma, factor=1):
    def err_func(x):
        return factor * x * rand.gauss(1, sigma)
    return err_func

def fixed_estimations(estimations):
    estimations_i = iter(estimations)
    def err_func(x):
        return next(estimations_i)
    return err_func

def simulator(jobs, scheduler_factory=schedulers.PS, size_estimation=identity):

    events = [(t, ARRIVAL, (jobid, size)) for jobid, t, size in jobs]
    heapify(events) # not needed if jobs are sorted by arrival time
    remaining = {} # mapping jobid to remaining size
    schedule = {} # mapping from jobid to resource ratio -- values
                  # should add up to <= 1
    scheduler = scheduler_factory()

    last_t = 0

    while events: # main loop

        t, event_type, event_data = heappop(events)

        delta = t - last_t
        
        # update remaining sizes

        for jobid, resources in schedule.items():
            remaining[jobid] -= delta * resources
            #assert remaining[jobid] > -eps

        # process event (and call the scheduler)

        if event_type == ARRIVAL:
            jobid, size = event_data
            remaining[jobid] = size
            scheduler.enqueue(t, jobid, size_estimation(size))
        elif event_type == COMPLETE:
            jobid = event_data
            #assert -eps <= remaining[jobid] <= eps
            yield t, jobid
            del remaining[jobid]
            scheduler.dequeue(t, jobid)
        schedule = scheduler.schedule(t)
        
        #assert sum(schedule.values()) < 1 + eps
        #assert not remaining or sum(schedule.values()) > 1 - eps
        #if (scheduler_factory.__name__ == 'PS'):
        #    assert set(schedule) == set(remaining)

        # if a job would terminate before next event, insert the
        # COMPLETE event

        next_int = scheduler.next_internal_event()
        if next_int is not None:
            next_time = t + next_int
            if (not events) or next_time < events[0][0]:
                heappush(events, (next_time, INTERNAL, None))
                     
        if remaining:
            completions = ((remaining[jobid] / resources, jobid)
                           for jobid, resources in schedule.items())
            try:
                next_delta, jobid = min(completions)
            except ValueError: # no scheduled items
                pass
            else:
                #if (scheduler_factory.__name__ == 'FSP'
                #    and size_estimation is identity):
                #    assert schedule == {jobid: 1}
                next_complete = t + next_delta
                if (not events) or events[0][0] > next_complete:
                    heappush(events, (next_complete, COMPLETE, jobid))

        last_t = t

    assert not remaining
