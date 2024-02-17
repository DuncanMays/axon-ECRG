from sys import path
path.append('..')

import axon
import asyncio
import time
import json
import pytest

default_service_depth = axon.config.default_service_depth
port = axon.config.comms_config.worker_port

# the endpoint that our service will be located at
endpoint = 'test_endpoint_prefix'
# the name of our service
service_name = 'simplex_service'

test_service_depth = 3

# this test manulually creates a stub that points to a service endpoint. Note that each endpoint is suffixed with /__call__ since RPC configs are stored on the __call__ attribute
@pytest.mark.asyncio
async def test_GenericStub():
	print('test_GenericStub')

	# tests that ServiceStubs, including child stubs, are instantiated properly and that their RPCs work
	full_endpoint = f'{endpoint}/{service_name}'
	for i in range(default_service_depth, 0, -1):
		print('testing GenericStub')

		url=f'http://localhost:{port}/{full_endpoint}/test_fn/__call__'
		stub = axon.stubs.GenericStub(url=url, tl=axon.transport_client.HTTPTransportClient())
		
		await stub()

		# next iteration, the stub will point at the child service
		full_endpoint = full_endpoint + '/child'

# this test creates a metastub to a test service and calls methods recursively to check each child object. Also checks inheritance from a BaseClass
@pytest.mark.asyncio
async def test_MetaServiceStub():
	print('test_MetaServiceStub')

	class BaseClass():
		def __init__(self):
			pass

	url = f'http://localhost:{port}/{endpoint}/{service_name}'
	worker = axon.client.get_ServiceStub(url, top_stub_type=BaseClass)

	# Tests that the stub is inherited from BaseClass, as specified by kwarg top_stub_type
	if isinstance(worker, BaseClass):
		print('Inheritance from BaseClass confirmed')
	else:
		raise BaseException('Stub is not inheritance from BaseClass')

	# tests that child stubs are instantiated properly and that their RPCs work
	for i in range(test_service_depth, 0, -1):
		await worker.test_fn()
		await worker()

		if isinstance(worker.test_fn, axon.stubs.GenericStub):
			print('RPC inheritance from axon.stubs.GenericStub confirmed')
		else:
			raise BaseException('RPC stub is not inheritance from axon.stubs.GenericStub')

		if isinstance(worker, axon.stubs.GenericStub):
			print('Callable stub inheritance from axon.stubs.GenericStub confirmed')
		else:
			raise BaseException('Callable stub is not inheritance from axon.stubs.GenericStub')

		if (i != 1):
			# if this is the last iteration, worker won't have a child and this line will raise an attribute error
			worker = worker.child

# this test creates a metastub to a test service that inherits from SimplexStubs and calls methods recursively to check that each child function is a sync stub
@pytest.mark.asyncio
async def test_SyncStub():
	print('test_SyncStub')

	url = f'http://localhost:{port}/{endpoint}/{service_name}'
	worker = axon.client.get_ServiceStub(url, stub_type=axon.stubs.SyncStub)

	# tests that child stubs are instantiated properly and that their RPCs work
	for i in range(test_service_depth, 0, -1):
		worker.test_fn()
		worker()

		# tests that stub is inherited from GenericSimplexStub
		if isinstance(worker.test_fn, axon.stubs.SyncStub):
			print('Inheritance from axon.stubs.SyncStub confirmed')
		else:
			raise BaseException('Stub is not inheritance from axon.stubs.SyncStub')

		if (i != 1):
			# if this is the last iteration, worker won't have a child and this line will raise an attribute error
			worker = worker.child