# test_api.py
import layer_cake as lc

class Xy(object):
	def __init__(self, x: int=1, y: int=1):
		self.x = x
		self.y = y

lc.bind(Xy)

table_type = lc.def_type(list[list[float]])
