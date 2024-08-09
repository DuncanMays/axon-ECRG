import sys
sys.path.append('..')

import axon

import random
import asyncio
import signal
import time
from threading import Thread

@axon.worker.rpc()
def print_msg(msg):
	print(msg)

@axon.worker.rpc()
def do_work(num_iters):
	msg='default'

	print('starting work')

	# the number of iterations that would take a second on my ideapad
	one_second = 44000000

	b = 1
	for i in range(num_iters*one_second):
		b = i*b

	print(msg)

	return random.randint(0, 10)

l = [1, 2, 3, 4]
s = axon.worker.register_ServiceNode(l, 'list_service')
s.add_child('list_child', [5,6,7])

def main():
	# starts the worker
	axon.worker.init()

	# port = 10_000
	# tlw = axon.config.transport.worker(port)

	# l = [1, 2, 3, 4]
	# s = axon.worker.ServiceNode(l, 'list_service', tl=tlw)
	# s.add_child('list_child', [5,6,7])

	# wrkr_thread = Thread(target=tlw.run, daemon=True)
	# wrkr_thread.start()
	# time.sleep(0.5)

	# s = axon.client.get_ServiceStub(f'localhost:{port}/list_service')

	# print(dir(s))

main()