from axon import axon
from types import SimpleNamespace

import pytest
import asyncio
import time

url_scheme = axon.config.url_scheme
TransportClient = type(axon.config.default_client_tl)
tl_config = axon.config.transport.config

@pytest.mark.tl
def test_tl_client():
	print('test_tl_client')

	rpc_name = 'simplex_rpc'
	url = f'{url_scheme}://localhost:{tl_config.port}/{axon.config.default_rpc_endpoint}/{rpc_name}/__call__'
	tl = TransportClient()

	assert('test passed!' == tl.call_rpc(url, ('test ', ), {'suffix':'passed!', }))

	url = f'{url_scheme}://localhost:{tl_config.port}{axon.config.default_service_config["endpoint_prefix"]}/_get_profile'
	profile = tl.call_rpc(url, (), {})

	assert('rpcs' in profile)
	assert('simplex_rpc' in profile['rpcs'])

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

@pytest.mark.asyncio
async def test_RemoteWorker():
	print('test_RemoteWorker')

	w = axon.client.get_RemoteWorker(f'{url_scheme}://localhost:{tl_config.port}')

	print(await w.rpcs.simplex_rpc('simplex test ', suffix='passed'))

	print(w.rpcs)

	# tests that the ServiceStub is set up right
	stub = w.simplex_service

	# tests that child stubs are instantiated properly and that their RPCs work
	for i in range(axon.config.default_service_depth, 0, -1):
		await w.simplex_service()
		w.simplex_service().join()

		await w.simplex_service.test_fn()
		w.simplex_service.test_fn().join()

		if isinstance(w.simplex_service, axon.stubs.GenericStub):
			print('Callable Stub inheritance from axon.stubs.GenericStub confirmed')
		else:
			raise BaseException('Callable Stub stub is not inheritance from axon.stubs.GenericStub')

		if isinstance(w.simplex_service.test_fn, axon.stubs.GenericStub):
			print('RPC inheritance from axon.stubs.GenericStub confirmed')
		else:
			raise BaseException('RPC stub is not inheritance from axon.stubs.GenericStub')

		if (i != 1):
			# if this is the last iteration, worker won't have a child and this line will raise an attribute error
			w.simplex_service = w.simplex_service.child