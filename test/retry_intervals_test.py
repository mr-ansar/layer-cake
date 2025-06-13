# retry_intervals_test.py
from unittest import TestCase
from datetime import timedelta
import layer_cake as lc

__all__ = [
	'TestRetryIntervals',
]

'''
'RetryIntervals',
'intervals_only',
'smart_intervals',

'''

def f(self):
	return

lc.bind(f)

class TestRetryIntervals(TestCase):
	def setUp(self):
		super().__init__()

	def tearDown(self):
		return super().tearDown()

	def test_retry_intervals(self):
		r = lc.RetryIntervals(first_steps=[0.5, 0.8, 0.95], regular_steps=1.0, step_limit=5)

		assert not r.empty()

		i = iter(lc.intervals_only(r))
		assert next(i) == 0.5
		assert next(i) == 0.8
		assert next(i) == 0.95
		assert next(i) == 1.0

		try:
			next(i)
		except StopIteration:
			pass

	def test_smart_intervals(self):
		r = lc.RetryIntervals(first_steps=[], regular_steps=5.0, step_limit=50, randomized=0.25, truncated=0.75)
		i = iter(lc.smart_intervals(r))
		for s in range(49):
			t = next(i)
			assert 5.0 <= t <= (5.0 + (5.0 * 0.75))

		try:
			next(i)
		except StopIteration:
			pass
