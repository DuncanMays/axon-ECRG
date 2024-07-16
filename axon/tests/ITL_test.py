import axon
import threading
import time
import pytest

from websockets.sync.client import connect
from concurrent.futures import ThreadPoolExecutor

url_scheme = axon.config.url_scheme
reflector = axon.ITL_reflector
ITL_Worker = axon.ITL_worker.ITL_Worker

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
	time.sleep(0.5)

	itlw = ITL_Worker(url='localhost', name='test_worker')
	tpe = ThreadPoolExecutor(max_workers=10)
	t = DummyClass()

	@axon.worker.rpc(tl=itlw, executor=tpe)
	def test_rpc(msg):
		return msg

	axon.worker.register_ServiceNode(t, 'test_service', tl=itlw, executor=tpe)

	worker_thread = threading.Thread(target=itlw.run, daemon=True)
	worker_thread.start()
	time.sleep(1)

	stub = axon.client.get_ServiceStub(f'{url_scheme}://localhost:{worker_port}/reflected_services')
	# print(stub[0].join())

	# url = f'{url_scheme}://localhost:{worker_port}/reflected_services'
	# dtl = axon.config.default_client_tl
	# profile = dtl.call_rpc(url, (), {})
	# print(profile.keys())

	time.sleep(1)

	reflected_str = 'this is a message sent from client to reflector, then to worker, where it\'s printed to console'
	# print(dir(stub))
	response = stub.test_worker.test_service.print_str(reflected_str).join()
	assert(response == 'all done!')

	response = stub.test_worker.rpc.test_rpc('test_msg').join()
	assert(response == 'test_msg')