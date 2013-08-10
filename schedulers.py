from __future__ import division

from collections import deque
from bisect import insort
from heapq import *

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
    def __init__(self, eps=0.001):
        self.queue = []    # heap of (attained, jobid) pairs for waiting jobs
        self.running = {}  # mapping to jobid to attained service for running
                           # jobs
        self.last_t = 0    # last time at which the schedule was changed
        self.eps = eps     # two jobs are considered to have attained the
                           # same service if they're within eps distance

    def enqueue(self, t, jobid, size):
        heappush(self.queue, (0, jobid))

    def dequeue(self, t, jobid):
        
        schedule = self.running
        try:
            del schedule[jobid]
        except KeyError:
            queue = self.queue
            try:
                idx = next(i for i, (_, jid) in enumerate(queue)
                           if jid == jobid)
            except StopIteration:
                raise ValueError("dequeuing missing job")
            else:
                del queue[idx]
                heapify(queue)
        else:
            delta = t - self.last_t
            service = delta / (len(schedule) + 1)
            for jid in schedule:
                schedule[jid] += service
            self.last_t = t

    def schedule(self, t):

        queue = self.queue
        schedule = self.running
        delta = t - self.last_t
        if schedule:
            service = delta / len(schedule)
            for jobid, attained in schedule.items():
                heappush(queue, (attained + service, jobid))
        
        new_schedule = {}
        try:
            threshold = queue[0][0] + self.eps
        except IndexError:
            # empty queue
            pass
        else:
            while queue and queue[0][0] <= threshold:
                attained, jobid = heappop(queue)
                new_schedule[jobid] = attained
        
        self.last_t = t
        self.running = new_schedule

        njobs = len(new_schedule)
        if njobs > 0:
            return {jobid: 1 / njobs for jobid in new_schedule}
        else:
            return {}

    def next_internal_event(self):

        schedule = self.running
        try:
            running_service = next(iter(schedule.values()))
        except StopIteration:
            # no jobs scheduled
            return None
        if self.queue:
            diff = self.queue[0][0] - running_service
            return self.last_t + diff / len(schedule)
        else:
            return None
        
