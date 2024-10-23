from axon import axon
from types import SimpleNamespace

import pytest
import asyncio
import time

url_scheme = axon.config.url_scheme
TransportClient = type(axon.config.default_client_tl)
tl_config = axon.config.transport.config

@pytest.fixture(scope='package')
def fix_basic_rpc():
	@axon.worker.rpc()
	def basic_rpc(prefix, suffix='basic test failed'):
		return prefix+suffix

@pytest.mark.tl
def test_tl_client(fix_basic_rpc):
	print('test_tl_client')

	rpc_name = 'basic_rpc'
	url = f'{url_scheme}://localhost:{tl_config.port}/{axon.config.default_rpc_endpoint}/{rpc_name}/__call__'
	tl = TransportClient()

	assert('test passed!' == tl.call_rpc(url, ('test ', ), {'suffix':'passed!', }))

	url = f'{url_scheme}://localhost:{tl_config.port}/{axon.config.default_service_config["endpoint_prefix"]}'
	profile = tl.call_rpc(url, (), {})

	assert('rpc' in profile)
	assert('basic_rpc' in profile['rpc'])

url_shorthand_test_cases = [('http://localhost:50/endpoint', 'http://localhost:50/endpoint'), ('http://localhost:50/endpoint', 'http://localhost/endpoint'), ('http://localhost:50/endpoint', 'localhost:50/endpoint'), ('http://localhost:50/endpoint', 'localhost/endpoint')]
url_shorthand_test_cases += [('http://192.168.2.0:50/endpoint', 'http://192.168.2.0:50/endpoint'), ('http://192.168.2.0:50/endpoint', 'http://192.168.2.0/endpoint'), ('http://192.168.2.0:50/endpoint', '192.168.2.0:50/endpoint'), ('http://192.168.2.0:50/endpoint', '192.168.2.0/endpoint')]
url_shorthand_test_cases += [('http://www.google.com:50/endpoint', 'http://www.google.com:50/endpoint'), ('http://www.google.com:50/endpoint', 'http://www.google.com/endpoint'), ('http://www.google.com:50/endpoint', 'www.google.com:50/endpoint'), ('http://www.google.com:50/endpoint', 'www.google.com/endpoint')]

@pytest.mark.parametrize("expected, shorthand", url_shorthand_test_cases)
def test_url_shorthand(expected, shorthand):
	print('test_url_shorthand')

	config = SimpleNamespace(
		port=50,
		scheme='http'
	)

	assert axon.stubs.add_url_defaults(shorthand, config) == expected

class RecursiveCallable():
	def __init__(self, depth=1):
		self.depth = depth

		if (depth>1):
			self.child = RecursiveCallable(depth=self.depth-1)
		else:
			self.child = None

	def test_fn(self):
		print(f'test_fn called at depth {self.depth}')

	def __call__(self):
		print(f'__call__ called at depth {self.depth}')

@pytest.fixture(scope='package')
def fix_basic_service():
	# the endpoint that our service will be located at
	endpoint = '/test_endpoint_prefix'

	# defines an instance of RecursiveCallable and creates a service node out of it
	test_service_depth = 3
	t_basic = RecursiveCallable(depth=test_service_depth)

	basic_service = axon.worker.register_ServiceNode(t_basic, 'basic_service', depth=test_service_depth, endpoint_prefix=endpoint)

@pytest.mark.asyncio
async def test_TopLevelServiceNode(fix_basic_service):
	print('test_TopLevelServiceNode')

	w = axon.client.get_ServiceStub(f'{url_scheme}://localhost:{tl_config.port}')

	print(await w.rpc.basic_rpc('basic test ', suffix='passed'))

	# tests that the ServiceStub is set up right
	stub = w.basic_service

	# tests that child stubs are instantiated properly and that their RPCs work
	for i in range(axon.config.default_service_depth, 0, -1):
		await w.basic_service()
		w.basic_service().join()

		await w.basic_service.test_fn()
		w.basic_service.test_fn().join()

		if isinstance(w.basic_service, axon.stubs.GenericStub):
			print('Callable Stub inheritance from axon.stubs.GenericStub confirmed')
		else:
			raise BaseException('Callable Stub stub is not inheritance from axon.stubs.GenericStub')

		if isinstance(w.basic_service.test_fn, axon.stubs.GenericStub):
			print('RPC inheritance from axon.stubs.GenericStub confirmed')
		else:
			raise BaseException('RPC stub is not inheritance from axon.stubs.GenericStub')

		if (i != 1):
			# if this is the last iteration, worker won't have a child and this line will raise an attribute error
			w.basic_service = w.basic_service.child