#
import random
import layer_cake as lc

random.seed()

def function(self, x: int=8, y: int=8) -> list[list[float]]:
	'''Generate a matrix[y][x] and fill with random values. Return a 2D table of floats.'''
	table = [[None] * x] * y

	for r in range(y):
		for c in range(x):
			table[r][c] = random.random()

	return table

# Register with runtime.
lc.bind(function)

# Optional process entry-point.
if __name__ == '__main__':
	lc.create(function)
