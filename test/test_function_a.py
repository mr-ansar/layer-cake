# test_function_a.py
# A function inside a module.
import random

# Initalize the random machinery.
random.seed()


def texture(x: int=8, y: int=8) -> list[list[float]]:
	'''Generate a matrix of random values. Return a 2D table of floats.'''

	table = []
	for r in range(y):
		row = [None] * x
		table.append(row)
		for c in range(x):
			row[c] = random.random()	# Populate table.

	return table
