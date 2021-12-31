from axon.worker import rpc, init

import time
import random

@rpc(comms_pattern='duplex', executor='Process')
def do_work(num_iters):
	# the number of iterations that would take a second on my ideapad
	one_second = 44000000

	print('starting work')

	b = 1
	for i in range(num_iters*one_second):
		b = i*b

	# time.sleep(num_iters)

	print('work completed')

	return random.randint(0, 10)

init()