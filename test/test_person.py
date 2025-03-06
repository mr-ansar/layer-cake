# object_startup_test.py
import layer_cake as lc


class Person(object):
	def __init__(self, given_name: str=None):
		self.given_name = given_name

lc.bind(Person)
