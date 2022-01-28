import sys
sys.path.append('..')

from axon import worker
from axon import discovery

import random
import asyncio
import signal

@worker.rpc(comms_pattern='duplex', executor='Process')
def do_work(num_iters, msg='default'):
	# the number of iterations that would take a second on my ideapad
	one_second = 44000000

	print('starting work')

	b = 1
	for i in range(num_iters*one_second):
		b = i*b

	print(msg)

	return random.randint(0, 10)

def main():

	# starts the worker
	worker.init()

main()