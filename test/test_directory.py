# test_directory.py
import layer_cake as lc

def directory(self):
	'''. Return.'''

	while True:
		m = self.input()
		if isinstance(m, lc.Stop):
			return lc.Aborted()

# Register with runtime.
lc.bind(directory)

# Optional process entry-point.
if __name__ == '__main__':
	lc.create(directory)
