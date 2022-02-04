import sys
sys.path.append('..')

from axon import worker

@worker.rpc()
def hello_world():
	print('hello')
	return 'world'

worker.init()