# test_caller.py
# Demonstration of the different calling conventions
# available to the developer.
import layer_cake as lc

from test_function import function

def caller(self, choice: int=0) -> list[list[float]]:
	if choice < 0 or choice > 2:
		return lc.Faulted(f'input out of range ({choice})')

	# Traditional function call.
	direct_call = function(self)

	# Multi-threaded.
	a = self.create(function, x=2, y=2)
	i, separate_thread, p = self.select(lc.Returned)

	# As a process.
	a = self.create(lc.ProcessObject, function, x=16, y=16)
	i, separate_process, p = self.select(lc.Returned)

	# Full set of results.
	returned = (
		direct_call,					# Straight from the call.
		separate_thread.original(),		# Extract from Returned.
		separate_process.original(),
	)
	# Return one of them.
	m = returned[choice]
	return m

lc.bind(caller)

if __name__ == '__main__':
	lc.create(caller)
