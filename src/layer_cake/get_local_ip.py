import socket

__all__ = [
	'get_local_ip',
]

LOCAL_NETWORKS = ('127.', '0:0:0:0:0:0:0:1')
IGNORED_NETWORKS = LOCAL_NETWORKS + ('0.', '0:0:0:0:0:0:0:0', '169.254.', 'fe80:')
TESTNET = '192.0.2.123'

def _get_local_ip(family, remote):
    try:
        s = socket.socket(family, socket.SOCK_DGRAM)
        try:
            s.connect((remote, 9))
            return s.getsockname()[0]
        finally:
            s.close()
    except socket.error:
        return None

def get_local_ip():
	local = _get_local_ip(socket.AF_INET, TESTNET)
	if not local:
		return None

	if local.startswith(IGNORED_NETWORKS):
		return None
	return local

