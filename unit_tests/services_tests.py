from sys import path
path.append('..')

import axon
import threading
import asyncio
import time
import json

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
endpoint = 'test_endpoint_prefix/'
# the name of our service
service_name = 'test_service'

# defines an instance of TestClass and creates a service node out of it
test_service_depth = 3
t = TestClass(depth=test_service_depth)
s = axon.worker.ServiceNode(t, service_name, depth=test_service_depth, endpoint_prefix=endpoint)

# creates a thread to run the worker in
worker_thread = threading.Thread(target=axon.worker.init, name='client_test.worker_thread')
worker_thread.daemon = True

async def test_basic_service_request():
	print('test_basic_service_request')

	stub = axon.stubs.SyncSimplexStub(worker_ip='localhost', endpoint_prefix=endpoint+service_name+'/', rpc_name='test_fn')
	stub()

	handle = stub.async_call((), {})
	handle.join()
	await stub.coro_call((), {})
	stub.sync_call((), {})

	stub = axon.stubs.SyncSimplexStub(worker_ip='localhost', endpoint_prefix=endpoint+service_name+'/child/', rpc_name='test_fn')
	stub()

	handle = stub.async_call((), {})
	handle.join()
	await stub.coro_call((), {})
	stub.sync_call((), {})

async def test_RemoteWorker_to_service():
	print('test_RemoteWorker_to_service')

	worker = axon.client.ServiceStub('localhost', endpoint_prefix=endpoint+service_name)

	for i in range(test_service_depth, 0, -1):
		await worker.test_fn()

		if (i != 1):
			# if this is the last iteration, worker won't have a child and this line will raise an attribute error
			worker = worker.child

async def test_MetaServiceStub():
	print('test_MetaServiceStub')

	class BaseClass():
		def __init__(self):
			pass

	worker = axon.client.get_MetaStub('localhost', endpoint_prefix=endpoint+service_name, parent_class=BaseClass)

	# Tests that the stub is inherited from BaseClass, as specified by kwarg parent_class
	if isinstance(worker, BaseClass):
		print('Inheritance from BaseClass confirmed')
	else:
		raise BaseException('Stub is not inheritance from BaseClass')

	# tests that child stubs are instantiated properly and that their RPCs work
	for i in range(test_service_depth, 0, -1):
		await worker.test_fn()

		# if i != test_service_depth:
		await worker()

		# tests that stub is inherited from GenericSimplexStub
		if isinstance(worker.test_fn, axon.stubs.GenericSimplexStub):
			print('Inheritance from axon.stubs.GenericSimplexStub confirmed')
		else:
			raise BaseException('Stub is not inheritance from axon.stubs.GenericSimplexStub')

		if (i != 1):
			# if this is the last iteration, worker won't have a child and this line will raise an attribute error
			worker = worker.child

async def main():
	worker_thread.start()
	# gives the worker a little time to start
	time.sleep(0.5)

	# await test_basic_service_request()

	await test_RemoteWorker_to_service()

	await test_MetaServiceStub()

if __name__ == '__main__':
	asyncio.run(main())