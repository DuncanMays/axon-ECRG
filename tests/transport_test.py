import pytest
import threading
import asyncio
import time

from sys import path
path.append('./')

import axon

class TestSimplex():

	@pytest.mark.asyncio
	async def test_coro_stub(self):
		print('test_coro_stub')

		rpc_name = 'simplex_rpc'
		url = 'http://localhost:'+str(axon.config.comms_config.worker_port)+'/'+axon.config.default_rpc_config['endpoint_prefix']+rpc_name+'/__call__'

		result = await axon.simplex_stubs.call_simplex_rpc_coro(url, ('test ', ), {'suffix':'passed!', })

		print(result)

	def test_async_stub(self):
		print('test_async_stub')

		rpc_name = 'simplex_rpc'
		url = 'http://localhost:'+str(axon.config.comms_config.worker_port)+'/'+axon.config.default_rpc_config['endpoint_prefix']+rpc_name+'/__call__'

		resultHandle = axon.simplex_stubs.call_simplex_rpc_async(url, ('test ', ), {'suffix':'passed!', })

		print(resultHandle.join())

	def test_sync_stub(self):
		print('test_sync_stub')

		rpc_name = 'simplex_rpc'
		url = 'http://localhost:'+str(axon.config.comms_config.worker_port)+'/'+axon.config.default_rpc_config['endpoint_prefix']+rpc_name+'/__call__'

		print(axon.simplex_stubs.call_simplex_rpc_sync(url, ('test ', ), {'suffix':'passed!', }))

class TestDuplex():

	@pytest.mark.asyncio
	async def test_coro_stub(self):
		print('test_coro_stub')

		rpc_name = 'duplex_rpc'
		url = 'http://localhost:'+str(axon.config.comms_config.worker_port)+'/'+axon.config.default_rpc_config['endpoint_prefix']+rpc_name+'/__call__'

		result = await axon.duplex_stubs.call_duplex_rpc_coro(url, ('test ', ), {'suffix':'passed!', })

		print(result)
	
	def test_async_stub(self):
		print('test_async_stub')

		rpc_name = 'duplex_rpc'
		url = 'http://localhost:'+str(axon.config.comms_config.worker_port)+'/'+axon.config.default_rpc_config['endpoint_prefix']+rpc_name+'/__call__'

		resultHandle = axon.duplex_stubs.call_duplex_rpc_async(url, ('test ', ), {'suffix':'passed!', })

		print(resultHandle.join())

	def test_sync_stub(self):
		print('test_sync_stub')

		rpc_name = 'duplex_rpc'
		url = 'http://localhost:'+str(axon.config.comms_config.worker_port)+'/'+axon.config.default_rpc_config['endpoint_prefix']+rpc_name+'/__call__'

		result = axon.duplex_stubs.call_duplex_rpc_sync(url, ('test ', ), {'suffix':'passed!', })

		print(result)