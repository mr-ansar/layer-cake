import ansar.connect as ar

class User(object):
	def __init__(self, name='', age=0, height=0.0):
		self.name = name
		self.age = age
		self.height = height

ar.bind(User)
	
def factorial(self, n):
	if n < 2:
		return 1
	a = self.create(factorial, n-1)
	m = self.select(ar.Completed)
	return n * m.value

ar.bind(factorial)

def main(self):
	n = 7
	s = self.create(factorial, n)
	m = self.select(ar.Completed)
	self.console(f'factorial {n}={m.value}')

ar.bind(main)

if __name__ == '__main__':
	ar.create_object(main)

