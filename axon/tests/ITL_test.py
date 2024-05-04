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

	reflector_thread = threading.Thread(target=reflector.run, args=('reflected_services',), daemon=True)
	reflector_thread.start()
	time.sleep(0.5)

	itlw = ITL_Worker('ws://localhost:8008', 'test_worker')
	tpe = ThreadPoolExecutor(max_workers=10)
	t = DummyClass()

	axon.worker.register_ServiceNode(t, 'test_service', tl=itlw, executor=tpe)

	worker_thread = threading.Thread(target=itlw.run, daemon=True)
	worker_thread.start()
	time.sleep(0.5)

	stub = axon.client.get_ServiceStub(f'{url_scheme}://localhost:8081/reflected_services')
	reflected_str = 'this is a message sent from client to reflector, then to worker, where it\'s printed to console'
	response = stub.test_worker.test_service.print_str(reflected_str).join()
	assert(response == 'all done!')