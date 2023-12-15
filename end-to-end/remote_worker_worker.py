from sys import path
path.append('..')

from axon import worker

@worker.rpc()
def fn_1(a):
	print(a)
	return 'this is a simplex function'

@worker.rpc(comms_pattern='duplex')
def fn_2(a):
	print(a)
	return 'this is a duplex function'

worker.init()