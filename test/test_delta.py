# test_storage.py
import layer_cake as lc

#
#
def delta(self, left_path: str=None, right_path: str=None) -> list[lc.Any]:
	'''.'''
	if left_path is None or right_path is None:
		return lc.Faulted('no storage specified.')

	lp = lc.storage_manifest(left_path)
	rp = lc.storage_manifest(right_path)

	m = [d for d in lc.storage_delta(lp[0], rp[0])]

	return m

lc.bind(delta)	# Register with the framework.



if __name__ == '__main__':	# Process entry-point.
	lc.create(delta)
