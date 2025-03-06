# Author: Scott Woods <scott.18.ansar@gmail.com>
# MIT License
#
# Copyright (c) 2025 Scott Woods
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
"""Management of the async runtime.

Ensure that the support for async operation is in place when the process
needs it. Ensure that support is cleared out during process termination.
"""
__docformat__ = 'restructuredtext'

import os
import tempfile
from .virtual_memory import *
from .virtual_codec import *
from .json_codec import *
from .noop_codec import *
from .file_object import *
from .point_runtime import *
from .home_role import *
from .process_object import *


def edit_settings(self, home):
	editor = os.getenv('LC_EDITOR') or 'vi'

	try:
		fd, name = tempfile.mkstemp()
		os.close(fd)

		# Prepare materials for editor.
		temporary = File(name, MapOf(Unicode(), Any()), decorate_names=False)
		temporary.store(home.settings())

		# Setup detection of change.
		modified = os.stat(name).st_mtime

		# Run the editor.
		a = self.create(Utility, editor, name)
		self.assign(a, editor)
		m = self.select(Completed, Faulted, Stop)
		if isinstance(m, Faulted):
			return m
		e = self.debrief()
		value = m.value
		if isinstance(value, Faulted):
			return value

		# Was the file modified?
		if os.stat(name).st_mtime == modified:
			return Faulted(f'settings not modified')

		# Validate contents and update the runtime.
		r = temporary.recover()
		home.settings.update(r)
	except (CodecError, OSError) as e:
		return Faulted(f'cannot update settings ({e})')
	finally:
		os.remove(name)
	return None

HR.edit_settings = edit_settings
