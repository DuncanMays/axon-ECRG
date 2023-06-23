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

simplex_service = axon.worker.ServiceNode(t, service_name, depth=test_service_depth, endpoint_prefix=endpoint)

duplex_service = axon.worker.ServiceNode(t, 'duplex_service', depth=test_service_depth, endpoint_prefix=endpoint, comms_pattern='duplex')

# creates a thread to run the worker in
worker_thread = threading.Thread(target=axon.worker.init, name='client_test.worker_thread')
worker_thread.daemon = True

# this test manulually creates a stub that points to a service endpoint. Note that each endpoint is suffixed with /__call__ since RPC configs are stored on the __call__ attribute
async def test_basic_service_request():
	print('test_basic_service_request')

	stub = axon.stubs.SyncSimplexStub(worker_ip='localhost', endpoint_prefix=endpoint+service_name+'/', rpc_name='test_fn/__call__')
	stub()

	handle = stub.async_call((), {})
	handle.join()
	await stub.coro_call((), {})
	stub.sync_call((), {})

	stub = axon.stubs.SyncDuplexStub(worker_ip='localhost', endpoint_prefix=endpoint+'duplex_service/', rpc_name='test_fn/__call__')
	stub()

	# handle = stub.async_call((), {})
	# handle.join()
	# await stub.coro_call((), {})
	# stub.sync_call((), {})

	# stub = axon.stubs.SyncSimplexStub(worker_ip='localhost', endpoint_prefix=endpoint+service_name+'/child/', rpc_name='test_fn/__call__')
	# stub()

	# handle = stub.async_call((), {})
	# handle.join()
	# await stub.coro_call((), {})
	# stub.sync_call((), {})

# this test creates a metastub to a test service and calls methods recursively to check each child object. Also checks inheritance froma BaseClass
async def test_MetaServiceStub():
	print('test_MetaServiceStub')

	class BaseClass():
		def __init__(self):
			pass

	worker = axon.client.get_ServiceStub('localhost', endpoint_prefix=endpoint+service_name, top_stub_type=BaseClass)

	# Tests that the stub is inherited from BaseClass, as specified by kwarg top_stub_type
	if isinstance(worker, BaseClass):
		print('Inheritance from BaseClass confirmed')
	else:
		raise BaseException('Stub is not inheritance from BaseClass')

	# tests that child stubs are instantiated properly and that their RPCs work
	for i in range(test_service_depth, 0, -1):
		await worker.test_fn()
		# await worker()

		if isinstance(worker.test_fn, axon.stubs.GenericSimplexStub):
			print('RPC inheritance from axon.stubs.GenericSimplexStub confirmed')
		else:
			raise BaseException('RPC stub is not inheritance from axon.stubs.GenericSimplexStub')

		if isinstance(worker, axon.stubs.GenericSimplexStub):
			print('Callable stub inheritance from axon.stubs.GenericSimplexStub confirmed')
		else:
			raise BaseException('Callable stub is not inheritance from axon.stubs.GenericSimplexStub')

		if (i != 1):
			# if this is the last iteration, worker won't have a child and this line will raise an attribute error
			worker = worker.child

# this test creates a metastub to a test service that inherits from SimplexStubs and calls methods recursively to check that each child function is a sync stub
async def test_SyncStub():
	print('test_SyncStub')

	worker = axon.client.get_ServiceStub('localhost', endpoint_prefix=endpoint+service_name, stub_type=axon.client.SyncSimplexStub)

	# tests that child stubs are instantiated properly and that their RPCs work
	for i in range(test_service_depth, 0, -1):
		worker.test_fn()
		worker()

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

	await test_basic_service_request()

	await test_MetaServiceStub()

	await test_SyncStub()

if __name__ == '__main__':
	asyncio.run(main())