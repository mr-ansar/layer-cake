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

"""Self-maintaining storage as a FIFO of files.

Creates and maintains a series of files where each
file contains a time-slice of logs. New lines are added
to the end of the latest file until that reaches a
maximum size. At which point a new file is "tacked on" at
the end. Oldest files are deleted as necessary.
"""
__docformat__ = 'restructuredtext'

import os
import time
import re

from .folder_object import *
from .convert_memory import *
from collections import deque

__all__ = [
	'LINES_IN_FILE',
	'FILES_IN_FOLDER',
	'RollingLog',
	'read_log',
]

#
#
YMDTHMSF = '([0-9]{4})h([0-9]{2})h([0-9]{2})T([0-9]{2})c([0-9]{2})c([0-9]{2})p([0-9]{3})'
naming_convention = re.compile(YMDTHMSF)

LINES_IN_FILE = 16384
FILES_IN_FOLDER = 512

class RollingLog(object):
	"""
	"""
	def __init__(self, path, lines_in_file=None, files_in_folder=None):
		self.path = path
		self.folder = Folder(path, re=YMDTHMSF, decorate_names=False)
		self.lines_in_file = lines_in_file or LINES_IN_FILE
		self.files_in_folder = files_in_folder or FILES_IN_FOLDER
		self.lines = 0

		flat = []
		for f in self.folder.matching():
			iso = f.replace('h', '-')
			iso = iso.replace('c', ':')
			iso = iso.replace('p', '.')
			a = [
				f,
				text_to_world(iso),
			]
			flat.append(a)

		flat.sort(key=lambda m: m[1])
		self.manifest = deque(flat)
		self.opened, _ = self.open_file(time.time())

	def log_time(self, t):
		second = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(t))
		fraction = '%.3f' % (t,)
		fraction = fraction[-3:]
		lt = '%s.%s' % (second, fraction)
		return lt

	def open_file(self, t):
		lt = self.log_time(t)
		hcp = lt.replace('-', 'h')
		hcp = hcp.replace(':', 'c')
		hcp = hcp.replace('.', 'p')
		path = os.path.join(self.folder.path, hcp)
		f = open(path, 'w')
		self.manifest.append([path, t])
		while len(self.manifest) > self.files_in_folder:
			a = self.manifest.popleft()
			os.remove(a[0])
		self.lines = 0
		return f, lt

	def close_file(self, opened):
		opened.close()

	def __call__(self, log):
		"""
		"""
		if self.lines < self.lines_in_file:
			lt = self.log_time(log.stamp)
		else:
			self.close_file(self.opened)
			self.opened, lt = self.open_file(log.stamp)

		name = log.name.split('.')[-1]
		state = log.state
		if state is None:
			line = '%s %s <%08x>%s - %s\n' % (lt, log.tag.value, log.address[-1], name, log.text)
		else:
			line = '%s %s <%08x>%s[%s] - %s\n' % (lt, log.tag.value, log.address[-1], name, state, log.text)
		self.opened.write(line)
		self.opened.flush()

		self.lines += 1
		return line
	#def __close__(self):
	#	"Proper termination of file-based logging."
	#	pass

def read_log(logs, begin, end, count):
	'''Coroutine that accepts a log folder, range and yields lines.'''

	# Get the collection of files and their
	# timestamps.
	folder = Folder(logs.path, re=YMDTHMSF, decorate_names=False)
	rolling = []
	for f in folder.matching():
		iso = f.replace('h', '-')
		iso = iso.replace('c', ':')
		iso = iso.replace('p', '.')
		d = text_to_world(iso)
		a = [
			os.path.join(folder.path, f),
			d,
		]
		rolling.append(a)

	if len(rolling) < 1:	   # Early exit if nothing there.
		return
	rolling.sort(key=lambda m: m[1])		# Put them in order.

	if end is not None and end < rolling[0][1]:	 # Timeframe before all records.
		return

	# Internal coroutines to handle file and line
	# scanning.
	def get_file():
		# Slide up to the file with the "nearest"
		# timestamp, i.e. the one before the file
		# that is after.
		n = len(rolling)
		if begin < rolling[0][1]:
			i = 0
		elif begin >= rolling[-1][1]:
			yield rolling[-1][0]
			return
		else:
			for i in range(n - 1):
				if rolling[i + 1][1] > begin:
					break

		# Yield the sequence of files starting
		# at i.
		for j in range(i, len(rolling)):
			yield rolling[j][0]

	def get_line(r):
		# Open and close the presented file. Yield
		# each line from the file along with the
		# timestamp in usable form.
		with open(r, 'r') as f:
			for line in f:
				# convert stamp 2023-01-03T19:23:51
				i = line.index(' ')
				t = line[:i]
				d = text_to_world(t)
				yield d, line

	# 3 variants on the querying of a log,
	# 1) from <begin> to <end>,
	# 2) from <begin> for <count> and
	# 3) from <begin> to end-of-log.
	if end is not None:
		for r in get_file():
			for d, l in get_line(r):
				if d < begin:
					continue
				if d < end:
					yield d, l
				else:
					return
	elif count is not None:
		for r in get_file():
			for d, l in get_line(r):
				if d < begin:
					continue
				if count == 0:
					return
				count -= 1
				yield d, l
	else:
		for r in get_file():
			for d, l in get_line(r):
				if d < begin:
					continue
				yield d, l
