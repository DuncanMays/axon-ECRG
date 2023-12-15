import sys
sys.path.append('..')

from axon import worker

@worker.rpc()
def print_return(a, b):
	print(a)
	return b

worker.init()








