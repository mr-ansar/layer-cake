# test_storage.py
import layer_cake as lc

#
#
def storage(self, disk_path: str=None) -> lc.StorageManifest:
	'''.'''
	if disk_path is None:
		return lc.Faulted('no storage specified.')

	m = lc.storage_manifest(disk_path)
	return m[0]

lc.bind(storage)	# Register with the framework.



if __name__ == '__main__':	# Process entry-point.
	lc.create(storage)
