from __future__ import division

from collections import deque
from bisect import insort
from heapq import *

import operator

class PS:
    def __init__(self):
        self.running = set()

    def enqueue(self, t, jobid, size):
        self.running.add(jobid)

    def dequeue(self, t, jobid):
        self.running.remove(jobid)

    def schedule(self, t):
        running = self.running
        if running:
            share = 1 / len(running)
            return {jobid: share for jobid in running}
        else:
            return {}

class FIFO:
    def __init__(self):
        self.jobs = deque()

    def enqueue(self, t, jobid, size):
        self.jobs.append(jobid)

    def dequeue(self, t, jobid):
        self.jobs.remove(jobid)

    def schedule(self, t):
        jobs = self.jobs
        if jobs:
            return {jobs[0]: 1}
        else:
            return {}

class SRPT:
    def __init__(self):
        self.jobs = []
        self.last_t = 0

    def update(self, t):
        delta = t - self.last_t
        if delta == 0:
            return
        jobs = self.jobs
        if jobs:
            jobs[0][0] -= delta
        self.last_t = t

    def enqueue(self, t, jobid, job_size):
        self.update(t)
        heappush(self.jobs, [job_size, jobid])

    def dequeue(self, t, jobid):
        jobs = self.jobs
        self.update(t)
        # common case: we dequeue the running job
        if jobid == jobs[0][1]:
            heappop(jobs)
        # we still care if we dequeue a job not running (O(n)) --
        # could be made more efficient, but still O(n) because of the
        # search, by exploiting heap properties (i.e., local heappop)
        else:
            print("dequeueing a non-running job", jobid)
            idx = next(i for i, v in jobs if v[1] == jobid)
            jobs[idx], jobs[-1] = jobs[-1], jobs[idx]
            jobs.pop()
            heapify(jobs)

    def schedule(self, t):
        self.update(t)
        jobs = self.jobs
        if jobs:
            return {jobs[0][1]: 1}
        else:
            return {}

class FSP:
    def __init__(self):
        self.v_remaining = [] # virtual PS -- sorted by simulated
                              # remaining work; could be made a better
                              # data structure
        self.running = set() # running & in the virtual PS
        self.late = [] # should have completed, but didn't: error in
                       # the estimation!
        self.last_t = 0 

    def update(self, t):

        delta = t - self.last_t
        if delta == 0:
            return

        v_remaining = self.v_remaining
        if v_remaining:
            fair_share = 1 / len(v_remaining) * delta
            while v_remaining and v_remaining[0][0] < fair_share:
                # a job terminates in the virtual PS
                remaining_work, jobid = v_remaining[0]
                del v_remaining[0] # O(n)!
                if v_remaining:
                    # redistribute excess work to other jobs in the queue
                    fair_share += ((fair_share - remaining_work)
                                   / len(v_remaining))
                if jobid in self.running:
                    self.running.remove(jobid)
                    self.late.append(jobid)
            for rw_jobid in v_remaining:
                rw_jobid[0] -= fair_share

        self.last_t = t

    def enqueue(self, t, jobid, size):
        self.update(t)
        self.running.add(jobid)
        insort(self.v_remaining, [size, jobid])

    def dequeue(self, t, jobid):
        self.update(t)
        try:
            self.running.remove(jobid)
        except KeyError:
            self.late.remove(jobid)

    def schedule(self, t):
        self.update(t)

        if self.late:
            return {self.late[0]: 1}
        elif self.running:
            jobid = next((rw, jobid)
                         for rw, jobid in self.v_remaining
                         if jobid in self.running)[1]
            return {jobid: 1}
        else:
            return {}

class FSP_plus_PS(FSP):
    def schedule(self, t):
        self.update(t)

        late = self.late
        if late:
            share = 1 / len(late)
            return {job: share for job in late}
        elif self.running:
            jobid = next((rw, jobid)
                         for rw, jobid in self.v_remaining
                         if jobid in self.running)[1]
            return {jobid: 1}
        else:
            return {}
