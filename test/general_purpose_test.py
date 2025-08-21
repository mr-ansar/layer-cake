# send_test.py
from unittest import TestCase
from datetime import timedelta
import layer_cake as lc

__all__ = [
	'TestGeneralPurpose',
]

def f(self):
	return

lc.bind(f)

class TestGeneralPurpose(TestCase):
	def setUp(self):
		super().__init__()

	def tearDown(self):
		return super().tearDown()

	def test_gas(self):
		g = lc.Gas(a=1, b='hi', c=4.2)
		v = getattr(g, 'a', None)
		assert isinstance(v, int)
		v = getattr(g, 'b', None)
		assert isinstance(v, str)
		v = getattr(g, 'c', None)
		assert isinstance(v, float)

	def test_breakpath(self):
		a, b, c = lc.breakpath('/tmp/x/y.ext')
		assert a == '/tmp/x'
		assert b == 'y'
		assert c == '.ext'

	def test_output_line(self):
		lc.output_line('/tmp/x/y.ext')
		lc.output_line('/tmp/x/y.ext', tab=1)
		lc.output_line('/tmp/x/y.ext', newline=False)
		lc.output_line('{x}', x=1)

	def test_short_delta(self):
		d = lc.short_delta(timedelta(days=1.0, seconds=10.0))
		assert d == '1d'
		d = lc.short_delta(timedelta(days=0.0, seconds=10.0))
		assert d == '10s'
		d = lc.short_delta(timedelta(days=0.0, seconds=0.25))
		assert d == '0.2s'

	def test_spread_out(self):
		t = lc.spread_out(42.0)
		assert 42.0 * 0.75 <= t <= 42.0 * 1.25
		t = lc.spread_out(42.0)
		assert 42.0 * 0.75 <= t <= 42.0 * 1.25
		t = lc.spread_out(42.0)
		assert 42.0 * 0.75 <= t <= 42.0 * 1.25
		t = lc.spread_out(42.0)
		assert 42.0 * 0.75 <= t <= 42.0 * 1.25
		t = lc.spread_out(42.0)
		assert 42.0 * 0.75 <= t <= 42.0 * 1.25
		t = lc.spread_out(42.0)
		assert 42.0 * 0.75 <= t <= 42.0 * 1.25

		t = lc.spread_out(42.0, delta=10)
		assert 42.0 * 0.9 <= t <= 42.0 * 1.1
		t = lc.spread_out(42.0, delta=10)
		assert 42.0 * 0.9 <= t <= 42.0 * 1.1
		t = lc.spread_out(42.0, delta=10)
		assert 42.0 * 0.9 <= t <= 42.0 * 1.1
		t = lc.spread_out(42.0, delta=10)
		assert 42.0 * 0.9 <= t <= 42.0 * 1.1
		t = lc.spread_out(42.0, delta=10)
		assert 42.0 * 0.9 <= t <= 42.0 * 1.1
		t = lc.spread_out(42.0, delta=10)
		assert 42.0 * 0.9 <= t <= 42.0 * 1.1
