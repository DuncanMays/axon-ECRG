import pytest
import threading
import asyncio
import time

from sys import path
path.append('..')

import axon

def test_error_wrappers():
	print('test_error_wrappers')

	def test_fn():
		raise(BaseException('this is the exception that is raised if everything works'))

	wrapped_fn = axon.comms_wrappers.error_wrapper(test_fn)

	return_obj = wrapped_fn((), {})

	try:
		axon.transport.error_handler(return_obj)
	except(BaseException):
		print('test passed')

class TestSimplex():

	@pytest.mark.asyncio
	async def test_coro_stub(self):
		print('test_coro_stub')

		rpc_name = 'simplex_rpc'
		url = 'http://localhost:'+str(axon.config.comms_config.worker_port)+'/'+axon.config.default_rpc_config['endpoint_prefix']+rpc_name+'/__call__'

		result = await axon.transport.call_simplex_rpc_coro(url, ('test ', ), {'suffix':'passed!', })

		print(result)

	def test_async_stub(self):
		print('test_async_stub')

		rpc_name = 'simplex_rpc'
		url = 'http://localhost:'+str(axon.config.comms_config.worker_port)+'/'+axon.config.default_rpc_config['endpoint_prefix']+rpc_name+'/__call__'

		resultHandle = axon.transport.call_simplex_rpc_async(url, ('test ', ), {'suffix':'passed!', })

		print(resultHandle.join())

	def test_sync_stub(self):
		print('test_sync_stub')

		rpc_name = 'simplex_rpc'
		url = 'http://localhost:'+str(axon.config.comms_config.worker_port)+'/'+axon.config.default_rpc_config['endpoint_prefix']+rpc_name+'/__call__'

		print(axon.transport.call_simplex_rpc_sync(url, ('test ', ), {'suffix':'passed!', }))

	@pytest.mark.asyncio
	async def test_urllib3_stub(self):
		print('test_urllib3_stub')

		rpc_name = 'simplex_rpc'
		url = 'http://localhost:'+str(axon.config.comms_config.worker_port)+'/'+axon.config.default_rpc_config['endpoint_prefix']+rpc_name+'/__call__'

		print(await axon.transport_client.call_rpc(url, ('test ', ), {'suffix':'passed!', }))