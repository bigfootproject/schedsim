from __future__ import division

from collections import deque
from bisect import insort
from heapq import *
from functools import reduce
from collections import OrderedDict
from math import ceil

from blist import sorteddict, blist

def intceil(x): # superfluous in Python 3, ceil is sufficient
	return int(ceil(x))

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
            return
        # we still care if we dequeue a job not running (O(n)) --
        # could be made more efficient, but still O(n) because of the
        # search, by exploiting heap properties (i.e., local heappop)
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

class SRPT_plus_PS(Scheduler):

    def __init__(self, eps=1e-6):
        self.jobs = []
        self.last_t = 0
        self.late = set()
        self.eps = eps

    def update(self, t):
        delta = t - self.last_t
        jobs = self.jobs
        delta /= 1 + len(self.late) # key difference with SRPT #1
        if jobs:
            jobs[0][0] -= delta
        while jobs and jobs[0][0] < self.eps:
            _, jobid = heappop(jobs)
            self.late.add(jobid)
        self.last_t = t

    def next_internal_event(self):
        jobs = self.jobs
        if not jobs:
            return None
        return jobs[0][0] * (1 + len(self.late))

    def schedule(self, t):
        self.update(t)
        jobs = self.jobs
        late = self.late
        scheduled = late.copy() # key difference with SRPT #2
        if jobs:
            scheduled.add(jobs[0][1])
        if not scheduled:
            return {}
        share = 1 / len(scheduled)
        return {jobid: share for jobid in scheduled}

    def enqueue(self, t, jobid, job_size):
        self.update(t)
        heappush(self.jobs, [job_size, jobid])
    
    def dequeue(self, t, jobid):
        self.update(t)
        late = self.late
        if jobid in late:
            late.remove(jobid)
            return
        # common case: we dequeue the running job
        jobs = self.jobs
        if jobid == jobs[0][1]:
            heappop(jobs)
            return
        # we still care if we dequeue a job not running (O(n)) --
        # could be made more efficient, but still O(n) because of the
        # search, by exploiting heap properties (i.e., local heappop)
        try:
            idx = next(i for i, v in jobs if v[1] == jobid)
        except StopIteration:
            raise ValueError("dequeuing missing job")
        jobs[idx], jobs[-1] = jobs[-1], jobs[idx]
        jobs.pop()
        heapify(jobs)
    

class FSP(Scheduler):

    def __init__(self, eps=1e-6):

        # [remaining, jobid] queue for the *virtual* scheduler
        self.queue = blist()
        
        # Jobs that should have finished in the virtual time,
        # but didn't in the real (happens only in case of estimation
        # errors)
        # Keys are jobids (ordered by the time they became late), values are
        # not significant.
        self.late = OrderedDict()

        # last time we run the schedule function
        self.last_t = 0

        # Jobs that are running in the real time
        self.running = set()

        # Jobs that have less than eps work to do are considered done
        # (deals with floating point imprecision)
        self.eps = eps


    def enqueue(self, t, jobid, size):
        self.update(t) # needed to age only existing jobs in the virtual queue
        insort(self.queue, [size, jobid])
        self.running.add(jobid)

    def dequeue(self, t, jobid):
        # the job remains in the virtual scheduler!
        self.running.remove(jobid)

        late = self.late
        if jobid in late:
        	late.pop(jobid)

    def update(self, t):

        delta = t - self.last_t

        queue = self.queue

        if queue:
            running = self.running
            late = self.late
            eps = self.eps
            fair_share = delta / len(queue)
            fair_plus_eps = fair_share + eps

            # jobs in queue[:idx] are done in the virtual scheduler
            idx = 0
            for vrem, jobid in queue:
                if vrem > fair_plus_eps:
                    break
                idx += 1
                if jobid in running:
                    late[jobid] = True
            if idx:
           	    del queue[:idx]

            if fair_share > 0:
            	for vrem_jobid in queue:
            		vrem_jobid[0] -= fair_share

        self.last_t = t

    def schedule(self, t):

        self.update(t)
        
        late = self.late
        if late:
            return {next(iter(late)): 1}

        running = self.running
        if not running:
        	return {}

        jobid = next(jobid for _, jobid in self.queue if jobid in running)
        return {jobid: 1}

    def next_internal_event(self):
    	
    	queue = self.queue
    	
    	if not queue:
    		return None
    	
    	return queue[0][0] * len(queue)
        
class FSP_plus_PS(FSP):

    def __init__(self, *args, **kwargs):

        FSP.__init__(self, *args, **kwargs)
        self.late = dict(self.late) # we don't need the order anymore!

    def schedule(self, t):

        self.update(t)

        late = self.late
        if late:
            share = 1 / len(late)
            return {jobid: share for jobid in late}

        running = self.running
        if not running:
        	return {}

        jobid = next(jobid for _, jobid in self.queue if jobid in running)
        return {jobid: 1}


class LAS(Scheduler):

    def __init__(self, eps=1e-6):
        
        # job attained service is represented as (real attained service // eps)
        # (not perfectly precise but avoids problems with floats)
        self.eps = eps

        # sorted dictionary for {attained: {jobid}}
        self.queue = sorteddict()

        # {jobid: attained} dictionary
        self.attained = {}

        # result of the last time the schedule() method was called 
        # grouped by {attained: [service, {jobid}]}
        self.scheduled = {}
        # This is the entry point for doing XXX + LAS schedulers:
        # it's sufficient to touch here

        # last time when the schedule was changed
        self.last_t = 0
        
    def enqueue(self, t, jobid, size):

        self.queue.setdefault(0, set()).add(jobid)
        self.attained[jobid] = 0

    def dequeue(self, t, jobid):

        att = self.attained.pop(jobid)
        q = self.queue[att]
        if len(q) == 1:
            del self.queue[att]
        else:
            q.remove(jobid)
        
    def update(self, t):

        delta = intceil((t - self.last_t) / self.eps)
        queue = self.queue
        attained = self.attained
        set_att = set(attained)

        for att, sub_schedule in self.scheduled.items():

            jobids = reduce(set.union, (jobids for _, jobids in sub_schedule))

            # remove jobs from queue

            try:
                q_att = queue[att]
            except KeyError:
            	pass # all jobids have terminated
            else:
                q_att -= jobids
                if not q_att:
                	del queue[att]


            # recompute attained values, re-put in queue,
            # and update values in attained

            for service, jobids in sub_schedule:

                jobids &= set_att # exclude completed jobs
                if not jobids:
                    continue
                new_att = att + intceil(service * delta)

                # let's coalesce pieces of work differing only by eps, to avoid rounding errors
                try:
                	new_att = next(v for v in [new_att, new_att - 1, new_att + 1] if v in queue)
                except StopIteration:
                	pass

                queue.setdefault(new_att, set()).update(jobids)
                for jobid in jobids:
                    attained[jobid] = new_att
        self.last_t = t

    def schedule(self, t):

        self.update(t)

        try:
            attained, jobids = self.queue.items()[0]
        except IndexError:
            service = 0
            jobids = set()
            self.scheduled = {}
        else:
            service = 1 / len(jobids)
            self.scheduled = {attained: [(service, jobids.copy())]}
        return {jobid: service for jobid in jobids}

    def next_internal_event(self):

        queue = self.queue

        if len(queue) >= 2:
            qitems = queue.items()
            running_attained, running_jobs = qitems[0]
            waiting_attained, _ = qitems[1]
            diff = waiting_attained - running_attained
            return diff * len(running_jobs) * self.eps
        else:
            return None