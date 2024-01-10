import pytest
import threading
import asyncio
import time

from sys import path
path.append('..')

import axon

@pytest.mark.asyncio
async def test_client():
	print('test_client')

	rpc_name = 'simplex_rpc'
	url = 'http://localhost:'+str(axon.config.comms_config.worker_port)+'/'+axon.config.default_rpc_endpoint+rpc_name+'/__call__'
	tl = axon.transport_client.HTTPTransportClient()

	assert('test passed!' == await tl.call_rpc(url, ('test ', ), {'suffix':'passed!', }))

	url = f'http://localhost:{axon.config.comms_config.worker_port}/{axon.config.default_service_config["endpoint_prefix"]}/_get_profile'
	# profile = tl.get_worker_profile('localhost', port=axon.config.comms_config.worker_port)
	profile = await tl.call_rpc(url, (), {})

	assert('rpcs' in profile)
	assert('simplex_rpc' in profile['rpcs'])