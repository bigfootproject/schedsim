from __future__ import division

from collections import deque
from bisect import insort
from heapq import *
from blist import sorteddict

import operator

class Scheduler:
    def next_internal_event(self):
        return None

class PS(Scheduler):
    def __init__(self):
        self.running = set()

    def enqueue(self, t, jobid, size):
        self.running.add(jobid)

    def dequeue(self, t, jobid):
        try:
            self.running.remove(jobid)
        except KeyError:
            raise ValueError("dequeuing missing job")

    def schedule(self, t):
        running = self.running
        if running:
            share = 1 / len(running)
            return {jobid: share for jobid in running}
        else:
            return {}

class FIFO(Scheduler):
    def __init__(self):
        self.jobs = deque()

    def enqueue(self, t, jobid, size):
        self.jobs.append(jobid)

    def dequeue(self, t, jobid):
        try:
            self.jobs.remove(jobid)
        except ValueError:
            raise ValueError("dequeuing missing job")

    def schedule(self, t):
        jobs = self.jobs
        if jobs:
            return {jobs[0]: 1}
        else:
            return {}

class SRPT(Scheduler):
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
            try:
                idx = next(i for i, v in jobs if v[1] == jobid)
            except StopIteration:
                raise ValueError("dequeuing missing job")
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

class FSP(Scheduler):
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
            try:
                self.late.remove(jobid)
            except ValueError:
                raise ValueError("dequeuing missing job")

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

class LAS(Scheduler):
    def __init__(self, eps=1e-6):
        
        # sorted dict of {attained: set(jobid)} for pending jobs
        # grouped by attained service.
        self.queue = sorteddict()
        
        # set of scheduled jobs and their attained service
        self.scheduled = (set(), None)

        # {jobid: attained] dictionary
        self.rev_q = {}

        # last time when the schedule was changed
        self.last_t = 0
        
        # to handle rounding errors, two jobs are considered at the
        # same service if they're within eps distance
        self.eps = eps

    def _insert_jobs(self, jobids, attained):
        "Not trivial, because you have to take into account eps"

        # update self.queue
        queue = self.queue
        keys = queue.keys()
        idx = keys.bisect(attained)
        eps = self.eps
        if idx > 0 and attained - keys[idx - 1] < eps:
            queue.values()[idx - 1].update(jobids)
            attained = keys[idx - 1]
        elif idx < len(keys) and keys[idx] - attained < eps:
            queue.values()[idx].update(jobids)
            attained = keys[idx]
        else:
            queue[attained] = jobids

        # update self.rev_q
        for jobid in jobids:
            self.rev_q[jobid] = attained

    def enqueue(self, t, jobid, size):
        self._insert_jobs({jobid,}, 0)

    def dequeue(self, t, jobid):
        try:
            attained = self.rev_q[jobid]
        except KeyError:
            raise ValueError("dequeuing missing job")

        q_attained = self.queue[attained]
        if len(q_attained) > 1:
            q_attained.remove(jobid)
        else:
            del self.queue[attained]
        del self.rev_q[jobid]
    
    def schedule(self, t):

        delta = t - self.last_t
        running, attained = self.scheduled
        
        if running:
            # Keep track of attained service for running jobs
            service = delta / len(running)
            new_attained = attained + service
            try:
                q_attained = self.queue[attained]
            except KeyError:
                pass
            else:
                remaining = q_attained - running
                if not remaining:
                    del self.queue[attained]
                else:
                    self.queue[attained] = remaining
                serviced = q_attained & running
                self._insert_jobs(serviced, new_attained)

        # find the new schedule
        try:
            attained, running = self.queue.items()[0]
            service = 1 / len(running)
        except IndexError: # empty queue
            attained, running, service = None, set(), None
        self.scheduled = running.copy(), attained
        
        self.last_t = t
        return {jobid: service for jobid in running}

    def next_internal_event(self):
        
        running, r_attained = self.scheduled
        if r_attained is None:
            # no jobs scheduled yet
            return None

        for attained, jobs in self.queue.items():
            diff = attained - r_attained
            if diff > 0:
                return self.last_t + diff / len(running)

        # if we get here, no next internal events
        return None
