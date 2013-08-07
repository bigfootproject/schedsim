import unittest as UT
import schedulers
import simulator


class TestScheduler(UT.TestCase):

  @classmethod
  def setUpClass(cls):
    if not hasattr(cls,'scheduler'):
      cls.skipTest(cls,reason='abstract TestScheduler class')

#  def setUp(self):
#    if not hasattr(self,'scheduler'):
#      self.skipTest(reason='abstract')

  def run_jobs(self,jobs,error=simulator.identity):
    return list(simulator.simulator(jobs,self.scheduler,error))

  def run_and_assertEqual(self,jobs,expected):
    self.assertEqual(self.run_jobs(jobs),expected)

  def run_with_estimations(self,jobs,estimations):
    f = simulator.fixed_estimations(estimations)
    result = self.run_jobs(jobs,error=f)
    return list(result)

  def test_empty(self):
    self.assertEqual(self.run_jobs([]),[])

  def test_one(self):
    result = self.run_jobs([("job1",0,10)])
    self.assertEqual(result,[(10,"job1")])


class TestFIFO(TestScheduler):
  scheduler = schedulers.FIFO

  def test_two(self):
    self.run_and_assertEqual([('job1',0,10),('job2',0,10)]
                           , [(10,'job1'),(20,'job2')])

  def test_two_delayed(self):
    self.run_and_assertEqual([('job1',0,10),('job2',5,10)]
                           , [(10,'job1'),(20,'job2')])


class TestPS(TestScheduler):
  scheduler = schedulers.PS

  def test_two(self):
    self.run_and_assertEqual([('job1',0,10),('job2',0,10)]
                            ,[(20,'job1'),(20,'job2')])

  def test_two_delayed(self):
    self.run_and_assertEqual([('job1',0,10),('job2',5,10)]
                           , [(15,'job1'),(20,'job2')])


class TestSRPT(TestScheduler):
  scheduler = schedulers.SRPT

  def test_two(self):
    self.run_and_assertEqual([('job1',0,20),('job2',0,10)]
                           , [(10,'job2'),(30,'job1')])

  def test_two_delayed(self):
    self.run_and_assertEqual([('job1',0,20),('job2',5,10)]
                           , [(15,'job2'),(30,'job1')])

  def test_starvation(self):
    self.run_and_assertEqual([('job1',0,15),
                              ('job2',0,10),
                              ('job3',10,10),
                              ('job4',20,10)]
                           , [(10,'job2'),
                              (20,'job3'),
                              (30,'job4'),
                              (45,'job1')])


class TestFSP(TestScheduler):
  scheduler = schedulers.FSP

  def test_two(self):
    self.run_and_assertEqual([('job1',0,20),('job2',0,10)]
                           , [(10,'job2'),(30,'job1')])

  def test_two_delayed(self):
    self.run_and_assertEqual([('job1',0,20),('job2',5,10)]
                           , [(15,'job2'),(30,'job1')])

  def test_starvation(self):
    self.run_and_assertEqual([('job1',0,15),
                              ('job2',0,10),
                              ('job3',10,10),
                              ('job4',20,10)]
                           , [(10,'job2'),
                              (25,'job1'),
                              (35,'job3'),
                              (45,'job4')])

  def test_error(self):
    jobs = [('job1',0,10),('job2',0,10)]
    result = self.run_with_estimations(jobs,[15,20])
    self.assertEqual(result,[(10,'job1'),(20,'job2')])


if __name__ == '__main__':
  UT.main(verbosity=2)
