# test_api.py
import layer_cake as lc
from enum import Enum

__all__ = [
	'table_type',
	'CallingConvention',
	'DEFAULT_CONVENTION',
	'Xy',
]

table_type = lc.def_type(list[list[float]])

class CallingConvention(Enum):
	CALL=1
	THREAD=2
	THREAD_SPOOL=3
	PROCESS=4
	LIBRARY=5
	PROCESS_SPOOL=6
	FLOOD=7
	SOAK=8

DEFAULT_CONVENTION = CallingConvention.CALL

class Xy(object):
	def __init__(self, x: int=1, y: int=1, convention: CallingConvention=DEFAULT_CONVENTION):
		self.x = x
		self.y = y
		self.convention = convention

lc.bind(Xy)

