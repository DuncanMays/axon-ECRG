import sys
sys.path.append('..')

from axon import worker

@worker.rpc(comms_pattern='duplex')
def hello_world():
	print('hello')
	return 'world'

worker.init()