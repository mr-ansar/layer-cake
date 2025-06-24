# test_function_3.py
import random

random.seed()

def texture(self, x: int=8, y: int=8) -> list[list[float]]:
	table = []
	for r in range(y):
		row = [None] * x
		table.append(row)
		for c in range(x):
			row[c] = random.random()

	return table
