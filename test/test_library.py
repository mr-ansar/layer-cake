# test_library.py
import layer_cake as lc
import test_caller


def library(self):
	# Errors, sessions and inbound client messages.
	while True:
		i, m, p = self.select(lc.Faulted,	# Something went wrong.
			lc.Stop,						# Intervention.
			bool,							# API.
		)

		if i == 0:					# Terminate with the error.
			return m
		elif i == 1:				# Terminate as requested.
			return lc.Aborted()

		if m == True:
			self.reply(lc.Ack())
		else:
			self.reply(lc.Nak())

lc.bind(library, api=(bool,))

if __name__ == '__main__':
	lc.create(library)
