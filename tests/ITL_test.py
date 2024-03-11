import axon
import threading
import time

from websockets.sync.client import connect
from concurrent.futures import ThreadPoolExecutor

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

	reflector_thread = threading.Thread(target=reflector.run, daemon=True)
	reflector_thread.start()
	time.sleep(1)

	itlw = ITL_Worker('ws://localhost:8080')
	tpe = ThreadPoolExecutor(max_workers=10)
	t = DummyClass()

	axon.worker.register_ServiceNode(t, 'test_service', tl=itlw, executor=tpe)

	worker_thread = threading.Thread(target=itlw.run, daemon=True)
	worker_thread.start()
	time.sleep(1)

	stub = axon.client.get_ServiceStub('http://localhost:8081/reflected_service')

	reflected_str = 'this is a message sent from client to reflector, then to worker, back through the reflector'
	response = stub.print_str(reflected_str).join()
	print(response)

	itlw.close()