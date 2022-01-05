import sys
sys.path.append('..')

from axon import worker
from axon import discovery

import random
import asyncio
import signal

# this IP address of the notice board that this worker will sign in and out of
notice_board_ip = '192.168.2.19'

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

def sigint_handler(a, b):
	discovery.sign_out(notice_board_ip)
	exit()

async def main():
	# signs into the notice board
	discovery.sign_in(notice_board_ip)
	print('sign in complete')

	# sets a handler to sign out of the notice board
	signal.signal(signal.SIGINT, sigint_handler)

	# starts the worker
	worker.init()

asyncio.run(main())