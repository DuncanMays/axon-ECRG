# import axon
import pytest
import threading
import time

from axon.socket_transport import client, worker
from axon.config import inline_executor

port = 8989
endpoint = '/socket_transport/first_test'

@pytest.fixture(scope="package")
def fix_worker_thread():
	tlw = worker(port)

	thread = threading.Thread(target=tlw.run, daemon=True)
	thread.start()
	time.sleep(1)

	return tlw, port

def test_basic(fix_worker_thread):

	(tlw, port) = fix_worker_thread

	def echo(x):
		return x

	tlw.register_RPC(echo, endpoint, inline_executor)

	tlc = client()
	result = tlc.call_rpc(f'ws://localhost:{str(port)}{endpoint}', (1,), {})
	assert result == 1
