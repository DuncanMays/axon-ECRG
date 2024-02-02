import pytest
import threading
import asyncio
import time

from sys import path
path.append('..')

import axon

@pytest.mark.asyncio
async def test_tl_basic():
	port = axon.utils.get_open_port(lower_bound=8001)
	tlw = axon.worker.HTTPTransportWorker(port)
	tlc = axon.client.HTTPTransportClient()

	def wrk_fn(param):
		return param

	config = {'name':'wrk_fn', 'endpoint_prefix':'test_tl_basic/', 'executor':axon.inline_executor.InlineExecutor()}
	tlw.register_RPC(wrk_fn, **config)

	wrkr_thread = threading.Thread(target=tlw.run, daemon=True)
	wrkr_thread.start()

	time.sleep(1)

	url = f'http://localhost:{port}/test_tl_basic/wrk_fn'
	result = await tlc.call_rpc(url, ('hello!', ), {})
	assert(result == 'hello!')

@pytest.mark.asyncio
async def test_second_tl():
	port = axon.utils.get_open_port(lower_bound=8002)
	tlw = axon.worker.HTTPTransportWorker(port)

	class TestClass():

		def __init__(self):
			pass

		def test_fn(self, param):
			return param

	t = TestClass()
	axon.worker.register_ServiceNode(t, 'test_second_tl_service',tl=tlw)

	worker_thread = threading.Thread(target=tlw.run, daemon=True)
	worker_thread.start()

	time.sleep(1)

	# the positive test that the service registered with the secondary transport layer exists
	ss = axon.client.get_ServiceStub(ip_addr='localhost', port=port, endpoint_prefix='/test_second_tl_service')
	result = await ss.test_fn('hi there!')
	assert(result == 'hi there!')

	# the negative test that the service registered with the secondary transport layer does not show up on the primary transport layer
	rw = axon.client.get_RemoteWorker('localhost')
	assert(hasattr(rw, 'test_second_tl_service') == False)

