# this file starts a thread with an axon worker in it, for the purposes of testing client code

import threading
import axon
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing
import psutil

@axon.worker.rpc()
def simplex_rpc(prefix, suffix='simplex test failed'):
	return prefix+suffix

@axon.worker.rpc()
def throw_error():
	raise BaseException('Calling this RPC will raise an error')

class TestClass():
	def __init__(self, depth=1):
		self.depth = depth

		if (depth>1):
			self.child = TestClass(depth=self.depth-1)
		else:
			self.child = None

	def test_fn(self):
		print(f'test_fn called at depth {self.depth}')

	def __call__(self):
		print(f'__call__ called at depth {self.depth}')

# the endpoint that our service will be located at
endpoint = '/test_endpoint_prefix'

# defines an instance of TestClass and creates a service node out of it
test_service_depth = 3
t_simplex = TestClass(depth=test_service_depth)

simplex_service = axon.worker.register_ServiceNode(t_simplex, 'simplex_service', depth=test_service_depth, endpoint_prefix=endpoint)

class InlineService():
	async def print_this_async(self, delay, message):
		loop = asyncio.get_event_loop()
		await asyncio.sleep(delay)
		return message

	def print_this(self, delay, message):
		time.sleep(delay)
		return message

ils = InlineService()
axon.worker.register_ServiceNode(ils, name='inline_service')

class ThreadPoolService():
	async def print_this_async(self, delay, message):
		loop = asyncio.get_event_loop()
		await asyncio.sleep(delay)
		return message

	def print_this(self, delay, message):
		time.sleep(delay)
		return message

tps = ThreadPoolService()
tpe = ThreadPoolExecutor(max_workers=10)
axon.worker.register_ServiceNode(tps, name='thread_pool_service', executor=tpe)

class ProcessPoolService():
	async def print_this_async(self, delay, message):
		loop = asyncio.get_event_loop()
		await asyncio.sleep(delay)
		return message

	def print_this(self, delay, message):
		time.sleep(delay)
		return message

tps = ProcessPoolService()
ppe = ProcessPoolExecutor(max_workers=10, mp_context=multiprocessing.get_context("spawn"))
axon.worker.register_ServiceNode(tps, name='process_pool_service', executor=ppe)

if (psutil.Process().name() == 'pytest'):
	# without this check, using the multiprocessing executor will result in this file being run more than once in other processes, and so we must check if we're in the main process before calling init

	worker_thread = threading.Thread(target=axon.worker.init, daemon=True, name='axon/tests/__init__.py')
	worker_thread.start()
	time.sleep(1)