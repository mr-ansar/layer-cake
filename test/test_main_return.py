# test_main_return.py
import layer_cake as lc

def main(self, return_an_int: bool=False, return_an_int_any: int=None):
	if return_an_int:
		return 42
	if return_an_int_any is not None:
		return (return_an_int_any, lc.Integer8())
	pass

lc.bind(main)

if __name__ == '__main__':
	lc.create(main)
