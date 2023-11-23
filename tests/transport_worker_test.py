from sys import path
path.append('..')

import threading
import axon

worker = axon.transport_worker

def fn(i, one=10):
	print('from transport_worker_test.py')
	return (i, one)

config = {
	'name': 'fn',
	'endpoint_prefix': '/'
}

# worker.register_RPC(fn, **config)

print('starting worker')
# worker.init()