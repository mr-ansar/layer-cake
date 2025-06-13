# rolling_log_test.py
from unittest import TestCase
import tempfile
import datetime
import layer_cake as lc
import layer_cake.rolling_log as rl

__all__ = [
	'TestRollingLog',
]

class TestRollingLog(TestCase):
	def setUp(self):
		self.temp_dir = tempfile.TemporaryDirectory()
		self.name = self.temp_dir.name
		lc.Folder(self.name)
		super().__init__()

	def tearDown(self):
		self.temp_dir.cleanup()
		return super().tearDown()

	def test_rolling(self):
		# CANT FLOOD THE LOG AND FORCE THE ROLLING BEHAVIOUR
		# COS IT TRIES TO CREATE MULTIPLE FILES WITH THE SAME
		# NAME!!!
		rolling = rl.RollingLog(self.name, lines_in_file=10, files_in_folder=10)
		rolling(lc.PointLog(stamp=lc.clock_now(), tag=lc.USER_TAG.CONSOLE, address=(1,), name='Hortense', text='blah'))
		rolling(lc.PointLog(stamp=lc.clock_now(), tag=lc.USER_TAG.CONSOLE, address=(1,), name='Hortense', text='blah'))
		rolling(lc.PointLog(stamp=lc.clock_now(), tag=lc.USER_TAG.CONSOLE, address=(1,), name='Hortense', text='blah'))
		rolling(lc.PointLog(stamp=lc.clock_now(), tag=lc.USER_TAG.CONSOLE, address=(1,), name='Hortense', text='blah'))
		rolling(lc.PointLog(stamp=lc.clock_now(), tag=lc.USER_TAG.CONSOLE, address=(1,), name='Hortense', text='blah'))
		rolling(lc.PointLog(stamp=lc.clock_now(), tag=lc.USER_TAG.CONSOLE, address=(1,), name='Hortense', text='blah'))
		rolling(lc.PointLog(stamp=lc.clock_now(), tag=lc.USER_TAG.CONSOLE, address=(1,), name='Hortense', text='blah'))
		rolling(lc.PointLog(stamp=lc.clock_now(), tag=lc.USER_TAG.CONSOLE, address=(1,), name='Hortense', text='blah'))
		rolling(lc.PointLog(stamp=lc.clock_now(), tag=lc.USER_TAG.CONSOLE, address=(1,), name='Hortense', text='blah'))
		rolling(lc.PointLog(stamp=lc.clock_now(), tag=lc.USER_TAG.CONSOLE, address=(1,), name='Hortense', text='blah'))

	def test_roll(self):
		rolling = rl.RollingLog(self.name, lines_in_file=10, files_in_folder=10)
		rolling.close_file(rolling.opened)
		rolling.opened, lt = rolling.open_file(lc.clock_now())

	def test_roll_over(self):
		rolling = rl.RollingLog(self.name, lines_in_file=10, files_in_folder=10)
		rolling.close_file(rolling.opened)
		rolling.opened, lt = rolling.open_file(lc.clock_now() - 2.0)
		del rolling

		rolling = rl.RollingLog(self.name, lines_in_file=10, files_in_folder=10)
		rolling.close_file(rolling.opened)
		rolling.opened, lt = rolling.open_file(lc.clock_now() - 1.0)
		del rolling

		rolling = rl.RollingLog(self.name, lines_in_file=10, files_in_folder=10)
		rolling.close_file(rolling.opened)
		rolling.opened, lt = rolling.open_file(lc.clock_now())
		del rolling

	def test_roll_over(self):
		rolling = rl.RollingLog(self.name, lines_in_file=10, files_in_folder=10)
		now = lc.clock_now()
		begin = now
		rolling(lc.PointLog(stamp=now, tag=lc.USER_TAG.CONSOLE, address=(1,), name='Hortense', text='blah'))
		rolling(lc.PointLog(stamp=now, tag=lc.USER_TAG.CONSOLE, address=(1,), name='Hortense', text='blah'))
		rolling(lc.PointLog(stamp=now, tag=lc.USER_TAG.CONSOLE, address=(1,), name='Hortense', text='blah'))
		rolling(lc.PointLog(stamp=now, tag=lc.USER_TAG.CONSOLE, address=(1,), name='Hortense', text='blah'))
		rolling(lc.PointLog(stamp=now, tag=lc.USER_TAG.CONSOLE, address=(1,), name='Hortense', text='blah'))
		rolling.close_file(rolling.opened)
		now = lc.clock_now() - 1.0
		rolling.opened, lt = rolling.open_file(now)
		rolling(lc.PointLog(stamp=now, tag=lc.USER_TAG.CONSOLE, address=(1,), name='Hortense', text='blah'))
		rolling(lc.PointLog(stamp=now, tag=lc.USER_TAG.CONSOLE, address=(1,), name='Hortense', text='blah'))
		rolling(lc.PointLog(stamp=now, tag=lc.USER_TAG.CONSOLE, address=(1,), name='Hortense', text='blah'))
		rolling(lc.PointLog(stamp=now, tag=lc.USER_TAG.CONSOLE, address=(1,), name='Hortense', text='blah'))
		rolling(lc.PointLog(stamp=now, tag=lc.USER_TAG.CONSOLE, address=(1,), name='Hortense', text='blah'))
		now = lc.clock_now() - 2.0
		rolling.opened, lt = rolling.open_file(now)
		rolling(lc.PointLog(stamp=now, tag=lc.USER_TAG.CONSOLE, address=(1,), name='Hortense', text='blah'))
		rolling(lc.PointLog(stamp=now, tag=lc.USER_TAG.CONSOLE, address=(1,), name='Hortense', text='blah'))
		rolling(lc.PointLog(stamp=now, tag=lc.USER_TAG.CONSOLE, address=(1,), name='Hortense', text='blah'))
		rolling(lc.PointLog(stamp=now, tag=lc.USER_TAG.CONSOLE, address=(1,), name='Hortense', text='blah'))
		rolling(lc.PointLog(stamp=now, tag=lc.USER_TAG.CONSOLE, address=(1,), name='Hortense', text='blah'))

		now = lc.world_now()
		now -= datetime.timedelta(seconds=5.0)
		read = [r for r in rl.read_log(rolling, now, None, None)]
		rewind = [r for r in rl.rewind_log(rolling, 15)]

		assert len(read) == 15
		assert len(rewind) == 15
