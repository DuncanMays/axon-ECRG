import pytest
import threading
import asyncio
import time

from sys import path
path.append('..')

import axon

class TestSimplex():

	@pytest.mark.asyncio
	async def test_urllib3_stub(self):
		print('test_urllib3_stub')

		rpc_name = 'simplex_rpc'
		url = 'http://localhost:'+str(axon.config.comms_config.worker_port)+'/'+axon.config.default_rpc_config['endpoint_prefix']+rpc_name+'/__call__'

		print(await axon.transport_client.call_rpc(url, ('test ', ), {'suffix':'passed!', }))