# test_directory.py
# Demonstration of builtin directory behaviour.
# Configuration happens on the command line, e.g. --connect-to-directory=<HostPort>
# Not available as sticky settings.
import layer_cake as lc

def directory(self):
	'''Hold the foreground while directory operates in the background. Return notification.'''

	while True:
		m = self.input()
		if isinstance(m, lc.Stop):
			return lc.Aborted()

# Register with runtime.
lc.bind(directory)

# Process entry-point.
if __name__ == '__main__':
	lc.create(directory)
