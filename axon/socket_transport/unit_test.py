import random
import pytest
import threading
import time

from websockets.sync.client import connect

from axon.socket_transport import client, worker, config
from axon.transport_client import AbstractTransportClient
from axon.config import inline_executor
from axon.chunking import send_in_chunks, recv_chunks

port = 8989

@pytest.fixture(scope="package")
def fix_worker_thread():
	tlw = worker(port)

	thread = threading.Thread(target=tlw.run, daemon=True)
	thread.start()
	time.sleep(1)

	return tlw, port

def test_basic(fix_worker_thread):

	endpoint = '/socket_transport/first_test'

	(tlw, port) = fix_worker_thread

	def echo(x):
		return x

	tlw.register_RPC(echo, endpoint, inline_executor)

	tlc = client()
	result = tlc.call_rpc(f'ws://localhost:{str(port)}{endpoint}', (1,), {})
	assert result == 1

def test_error(fix_worker_thread):

	(tlw, port) = fix_worker_thread
	endpoint = '/socket_transport/test_error'

	err_str = "this is an error that is thrown in a test"

	def throw_err():
		raise BaseException(err_str)

	tlw.register_RPC(throw_err, endpoint, inline_executor)

	tlc = client()

	with pytest.raises(BaseException) as err:
		tlc.call_rpc(f'ws://localhost:{str(port)}{endpoint}', (), {})

	assert str(err.value) == err_str

def test_huge_msg(fix_worker_thread):

	endpoint = '/socket_transport/test_huge_msg'

	(tlw, port) = fix_worker_thread

	# creates a large random string to test if the chunking feature is working
	msg_size = 1_000_000
	msg = ''.join([str(random.randint(0,9)) for i in range(msg_size)])

	def big_echo(x):
		return x

	tlw.register_RPC(big_echo, endpoint, inline_executor)

	tlc = client()
	result = tlc.call_rpc(f'ws://localhost:{str(port)}{endpoint}', (msg,), {})
	assert result == msg

# def test_bad_header(fix_worker_thread):

# 	endpoint = '/socket_transport/test_bad_header'

# 	(tlw, port) = fix_worker_thread

# 	# creates a large random string to test if the chunking feature is working
# 	msg_size = 1_000_000
# 	msg = ''.join([str(random.randint(0,9)) for i in range(msg_size)])

# 	def test_bad_header(x):
# 		return x

# 	tlw.register_RPC(test_bad_header, endpoint, inline_executor)

# 	# a mock transport client to intentionally send faulty input to see how the worker responds
# 	class MockTransportClient(AbstractTransportClient):

# 		def __init__(self, port=config.port):
# 			super().__init__()

# 		def get_config(self):
# 			return config

# 		def net_call(self, url, param_str):

# 			# split the endpoint from the url
# 			url_components = url.split('/')
# 			url_head = '/'.join(url_components[:3])		
# 			endpoint = '/' + '/'.join(url_components[3:])

# 			with connect(url_head) as socket:

# 				socket.send("faulty input")
				
# 				result_str = recv_chunks(socket)

# 			return result_str

# 	tlc = MockTransportClient()
# 	result = tlc.call_rpc(f'ws://localhost:{str(port)}{endpoint}', (msg,), {})
# 	assert result == msg