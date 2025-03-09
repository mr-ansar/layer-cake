# test_main.py
import layer_cake as lc

def main(self, message: str=None):
	message = message or 'Hello world'
	self.console(message)

lc.bind(main)

if __name__ == '__main__':
	lc.create(main)
