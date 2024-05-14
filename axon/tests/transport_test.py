import pytest
import threading
import asyncio
import time

import axon

url_scheme = axon.config.url_scheme
TransportClient = type(axon.config.default_client_tl)
TransportWorker = type(axon.config.default_service_config['tl'])

@pytest.mark.tl
def test_interface_compliance():

	assert(hasattr(axon.config.transport.config, 'port'))
	assert(hasattr(axon.config.transport.config, 'scheme'))

	assert(isinstance(axon.config.default_client_tl, axon.transport_client.AbstractTransportClient))
	assert(isinstance(axon.config.default_service_config['tl'], axon.transport_worker.AbstractTransportWorker))

@pytest.mark.tl
@pytest.mark.asyncio
async def test_tl_basic():

	port = axon.utils.get_open_port(lower_bound=8001)
	tlw = TransportWorker(port)
	tlc = TransportClient()

	def wrk_fn(param):
		return param

	tlw.register_RPC(wrk_fn, '/test_tl_basic/wrk_fn', axon.inline_executor.InlineExecutor())

	wrkr_thread = threading.Thread(target=tlw.run, daemon=True)
	wrkr_thread.start()

	time.sleep(0.5)

	url = f'{url_scheme}://localhost:{port}/test_tl_basic/wrk_fn'
	result = await tlc.call_rpc(url, ('hello!', ), {})
	assert(result == 'hello!')

@pytest.mark.tl
@pytest.mark.asyncio
async def test_error_catching():
	url = f'{url_scheme}://localhost:{axon.config.transport.config.port}/rpc'
	ss = axon.client.get_ServiceStub(url)

	with pytest.raises(BaseException):
		await ss.throw_error()

@pytest.mark.tl
@pytest.mark.asyncio
async def test_second_tl():

	port = axon.utils.get_open_port(lower_bound=8002)
	tlc = TransportClient()
	tlw = TransportWorker(port)

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
	url = f'{url_scheme}://localhost:{port}/test_second_tl_service'
	ss = axon.client.get_ServiceStub(url, tl=tlc)
	result = await ss.test_fn('hi there!')
	assert(result == 'hi there!')

	# the negative test that the service registered with the secondary transport layer does not show up on the primary transport layer
	rw = axon.client.get_RemoteWorker(f'{url_scheme}://localhost:{axon.config.transport.config.port}')
	assert(hasattr(rw, 'test_second_tl_service') == False)

