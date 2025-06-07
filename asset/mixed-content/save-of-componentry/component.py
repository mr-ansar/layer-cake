# Author: Scott Woods <scott.suzuki@gmail.com>
# MIT License
#
# Copyright (c) 2017-2022
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""A component template.

Blah.
"""
import sys
import ansar.create as ar
from component_if import ProcessSettings, ProcessReturned

# A standard component.
# Define the compiled defaults. Then run an instance of the specified object, passing
# the default args. The framework updates the args from stdin or the command line, as
# appropriate.

def main(self, settings, version):	# Or a store() method on self?
	# Version management.
	# Normal, specific version
	# and unsupported.
	if version is None:
		pass
	elif version == 'x.x':
		pass
	else:
		ar.unsupported_version(version)

	# On to the real application. Creating, sending,
	# completing and updating its persistent image.

	ar.home().store()

	if settings.steps > 0:
		settings.steps -= 1
		a = self.create(ar.Process, 'component', settings)
		m = self.select(ar.Completed, ar.Stop)
		if isinstance(m, ar.Stop):
			self.send(ar.Stop(), a)
			self.select(ar.Completed)
			return ar.Aborted()

		# Process the return from proper completion of a
		# sub-process. This is always a decoding (a, v)
		# tuple to give the parent process the opportunity
		# to respond to out-of-sync child process. Ignored
		# here.
		v = m.value
		if isinstance(v, tuple):	# From the child process.
			return v[0]
		return v		# From the local Process object, e.g. Faulted.
	else:
		self.start(ar.T1, 10)
		m = self.select(ar.T1, ar.Stop)
		if isinstance(m, ar.Stop):
			return ar.Aborted()

	# The return of the final process in the
	# chain.
	return ProcessReturned()
	# return ar.Faulted(condition='just a', explanation=' test')

ar.bind(main)

#
#
settings = ProcessSettings()		# Compiled defaults. In this case the class defaults.

if __name__ == '__main__':
	ar.run(main, settings)

