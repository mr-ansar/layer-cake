# test_api.py
import layer_cake as lc
from enum import Enum

__all__ = [
	'table_type',
	'CallingConvention',
	'DEFAULT_CONVENTION',
	'CreateTable',
]

table_type = lc.def_type(list[list[float]])

class CallingConvention(Enum):
	CALL=1
	THREAD=2
	PROCESS=3
	LIBRARY=4

DEFAULT_CONVENTION = CallingConvention.CALL

class CreateTable(object):
	def __init__(self, x: int=1, y: int=1, convention: CallingConvention=DEFAULT_CONVENTION):
		self.x = x
		self.y = y
		self.convention = convention

lc.bind(CreateTable)

