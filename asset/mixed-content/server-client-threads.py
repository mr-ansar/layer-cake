import ansar.connect as ar

class User(object):
	def __init__(self, name='', age=0, height=0.0):
		self.name = name
		self.age = age
		self.height = height

ar.bind(User)
	
def server(self):
	any = ar.HostPort('127.0.0.1', 0)
	ar.listen(self, any)
	listening = self.select(ar.Listening)
	self.send(listening.listening_ipp, self.parent_address)
	accepted = self.select(ar.Accepted)
	user = self.select(User)
	self.console(f'Hi {user.name}, are you really {user.height}m tall?')
	self.select(ar.Abandoned)
	self.select(ar.Stop)

ar.bind(server)

def client(self, address):
	ar.connect(self, address)
	connected = self.select(ar.Connected)
	server = self.return_address
	self.send(User(name='Cheryl', height=1.5), server)
	self.send(ar.Close(), server)
	self.select(ar.Closed)

ar.bind(client)

def main(self):
	s = self.create(server)
	address = self.select(ar.HostPort)
	c = self.create(client, address)
	self.select(ar.Completed)
	self.send(ar.Stop(), s)
	self.select(ar.Completed)

ar.bind(main)

if __name__ == '__main__':
	ar.create_object(main)

