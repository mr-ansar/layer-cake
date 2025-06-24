# test_function_1.py
import random
import layer_cake as lc

random.seed()

def texture(self, x: int=8, y: int=8) -> list[list[float]]:
	table = []
	for r in range(y):
		row = [None] * x
		table.append(row)
		for c in range(x):
			row[c] = random.random()

	return table

lc.bind(texture)

if __name__ == '__main__':
	lc.create(texture)
