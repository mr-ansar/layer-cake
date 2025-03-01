# Use the cheetah template library to replace names with values from
# the command line.
#
# $ python3 cheetah-replace.py <cheetah-template> a=10 b=passing c=ready
import sys
import json
from Cheetah.Template import Template

def program():
	return sys.argv[0]

def decode_json(a):
	if a is None:
		return str()
	return json.loads(a)

# Accepts either a list or a table distinguished by the
# presence of a newline. Commas are separators and newlines
# are terminators, i.e. the newline terminating a table
# is expected and the dangling row after split() is always
# cleaned off.
def comma_separated(a):
	f = a.find('\n')
	if f == -1:
		line = a.split(',')
		for x, column in enumerate(line):
			line[x] = decode_json(column)
		return line
	table = [t.split(',') for t in a.split('\n')]
	if len(table[-1]) == 0:
		table.pop()
	for y, row in enumerate(table):
		for x, column in enumerate(row):
			table[y][x] = decode_json(column)
	return table

def k_equals_v(a):
	if a.startswith('--'):
		c = comma_separated
		a = a[2:]
	elif a.startswith('-'):
		c = decode_json
		a = a[1:]
	else:
		c = lambda t: t
	i = a.index('=')	# Exception if its not there.
	k = a[0: i]
	t = a[i + 1:]
	v = c(t)
	return k, v

def main():
	if len(sys.argv) < 3:
		sys.stderr.write(f'{program()}: need a template and at least one k=v argument\n')
		sys.exit(49)

	name = sys.argv[1]
	with open(name) as f:
		tmpl = f.read()

	kv = {}
	for a in sys.argv[2:]:
		k, v = k_equals_v(a)
		kv[k] = v
	t = Template(tmpl, searchList=[kv])
	# Print only whats in the template.
	print(t, end='')

if __name__ == '__main__':
	main()
