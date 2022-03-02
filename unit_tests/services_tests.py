from sys import path
path.append('..')

import axon
import threading
import asyncio
import time
import json

class TestClass():
	def __init__(self, arg, kwarg='default', depth=1):
		self.arg = arg
		self.kwarg = kwarg
		self.depth = depth
		self.child = None

		if (depth>1):
			self.child = TestClass(self.arg, kwarg=self.kwarg, depth=self.depth-1)

	def test_fn(self):
		print(f'test_fn called at depth {self.depth}')

# defines an instance of TestClass and creates a service node out of it
t = TestClass('arg', kwarg='kwarg', depth=2)
s = axon.services.ServiceNode(t, 'test', endpoint_prefix='test_class/')

# creates a thread to run the worker in
worker_thread = threading.Thread(target=axon.worker.init, name='client_test.worker_thread')
worker_thread.daemon = True

async def test_basic_service_request():
	print('test_basic_service_request')

	stub = axon.simplex_stubs.SyncSimplexStub(worker_ip='localhost', endpoint_prefix='test_class/', rpc_name='test_fn')
	stub()

	handle = stub.async_call((), {})
	handle.join()
	await stub.coro_call((), {})
	stub.sync_call((), {})

	stub = axon.simplex_stubs.SyncSimplexStub(worker_ip='localhost', endpoint_prefix='test_class/child/', rpc_name='test_fn')
	stub()

	handle = stub.async_call((), {})
	handle.join()
	await stub.coro_call((), {})
	stub.sync_call((), {})

async def test_RemoteWorker_to_service():
	print('test_RemoteWorker_to_service')

	worker = axon.client.RemoteWorker('localhost')

	# print(worker.rpcs)
	# print(dir(worker.rpcs))

async def main():
	worker_thread.start()
	# gives the worker a little time to start
	time.sleep(0.1)

	await test_basic_service_request()

	await test_RemoteWorker_to_service()

if __name__ == '__main__':
	asyncio.run(main())