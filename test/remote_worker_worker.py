import sys
sys.path.append('..')

from axon import worker

@worker.rpc()
def fn_1(a):
	print(a)
	return 'this is simplex_fn'

@worker.rpc(comms_pattern='duplex')
def fn_2(a):
	print(a)
	return 'this is duplex_fn'

worker.init()