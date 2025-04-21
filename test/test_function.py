# test_function.py
import random
import layer_cake as lc

random.seed()


def texture(self, x: int=8, y: int=8) -> list[list[float]]:
	'''Generate a matrix and fill with random values. Return a 2D table of floats.'''

	table = [[None] * x] * y			# Table of nulls.
	for r in range(y):
		row = table[r]
		for c in range(x):
			row[c] = random.random()	# Populate table.

	return table

lc.bind(texture)			# Register with framework.

if __name__ == '__main__':	# Process entry-point.
	lc.create(texture)
