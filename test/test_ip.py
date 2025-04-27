# test_api.py

# A basic technique for managing ports used during
# unit testing. All ports start at the number below.
# Each test module that needs to use network ports
# is assigned a 25-port block, i.e. the 4th module
# has this line at the top;
# TEST_PORT = TEST_PORT_START + 75
# and then each unit test uses the notation;
# listen(self, HostPort('127...', TEST_PORT + 1))
# where the additional index refers to a slot
# within the block of 25.

__all__ = [
	'TEST_PORT_START',
]

# Somewhere in the dynamic, private, ephemeral space.
TEST_PORT_START = 55195
