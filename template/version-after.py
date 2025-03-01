# Use the cheetah template library to replace names with values from
# the command line.
#
# $ python3 cheetah-replace.py <cheetah-template> a=10 b=passing c=ready
import sys
import re
from Cheetah.Template import Template

def program():
	return sys.argv[0]

def bump_build(breakdown, tag):
	after = breakdown[2] + 1
	if tag:
		return f'{breakdown[0]}.{breakdown[1]}.{after}{tag}'
	return f'{breakdown[0]}.{breakdown[1]}.{after}'

def bump_minor(breakdown, tag):
	after = breakdown[1] + 1
	if tag:
		return f'{breakdown[0]}.{after}.0{tag}'
	return f'{breakdown[0]}.{after}.0'

def bump_major(breakdown, tag):
	after = breakdown[0] + 1
	if tag:
		return f'{after}.0.0{tag}'
	return f'{after}.0.0'

def main():
	if len(sys.argv) < 2:
		sys.stderr.write(f'{program()}: need at least a current version\n')
		sys.exit(49)

	current = sys.argv[1]
	dfa = re.compile(r'(\d+)\.(\d+)\.(\d+)([-._0-9A-Za-z]+)?')
	match = dfa.match(current)
	if not match:
		sys.stderr.write(f'{program()}: current version "{current}" does not breakdown\n')
		sys.exit(49)
	breakdown = [int(match[1]), int(match[2]), int(match[3])]

	bump = bump_build
	tag = None
	for a in sys.argv[2:]:
		if a.startswith('--'):
			equals = a.find('=')
			if equals == -1:
				flag = a[2:]
				value = None
			else:
				flag = a[2:equals]
				value = a[equals+1:]

			if flag == 'minor-version':
				bump = bump_minor
			elif flag == 'major-version':
				bump = bump_major
			elif flag == 'build-tag':
				tag = value

	print(bump(breakdown, tag), end='')

if __name__ == '__main__':
	main()
