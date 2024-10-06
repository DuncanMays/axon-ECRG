import axon
import threading
import time
import pytest
import random

from concurrent.futures import ThreadPoolExecutor

url_scheme = axon.config.url_scheme
reflector = axon.reflector

class DummyClass():

	def __init__(self):
		pass

	def print_str(self, str):
		print('===========================')
		print(f"here's the string: {str}")
		print('===========================')

		return 'all done!'

def test_basic_operation():

	worker_port=8081
	reflector_thread = threading.Thread(target=reflector.run, kwargs={'http_port':worker_port}, daemon=True)
	reflector_thread.start()
	time.sleep(1)

	itlw = reflector.ITLW(url='localhost', name='test_worker')
	tpe = ThreadPoolExecutor(max_workers=10)
	t = DummyClass()

	@axon.worker.rpc(tl=itlw, executor=tpe)
	def test_rpc(msg):
		return msg

	@axon.worker.rpc(tl=itlw, executor=tpe)
	def return_big_string():
		msg_size = 500_000
		msg = ''.join([str(random.randint(0,9)) for i in range(msg_size)])
		return msg

	axon.worker.register_ServiceNode(t, 'test_service', tl=itlw, executor=tpe)

	worker_thread = threading.Thread(target=itlw.run, daemon=True)
	worker_thread.start()
	time.sleep(1)

	stub = axon.client.get_ServiceStub(f'{url_scheme}://localhost:{worker_port}/reflected_services')

	reflected_str = 'this is a message sent from client to reflector, then to worker, where it\'s printed to console'
	response = stub.test_worker.test_service.print_str(reflected_str).join()
	assert(response == 'all done!')

	response = stub.test_worker.rpc.test_rpc('test_msg').join()
	assert(response == 'test_msg')

	stub.test_worker.rpc.return_big_string().join()