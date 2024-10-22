import axon
import threading
import time
import pytest
import random
import cloudpickle

from PIL import Image
from PIL import ImageChops
from concurrent.futures import ThreadPoolExecutor

refl_http_port=8081
tpe = ThreadPoolExecutor(max_workers=10)

@pytest.fixture(scope='package')
def refl_thread():

	reflector_thread = threading.Thread(target=axon.reflector.run, kwargs={'http_port':refl_http_port}, daemon=True)
	reflector_thread.start()
	time.sleep(1)

class DummyClass():

	def __init__(self):
		pass

	def print_str(self, str):
		print('===========================')
		print(f"here's the string: {str}")
		print('===========================')

		return 'all done!'

@pytest.fixture(scope='package')
def test_service(refl_thread):

	itlw = axon.reflector.ITLW(url='localhost', name='test_service')

	axon.worker.register_ServiceNode(DummyClass(), 'test_service', tl=itlw, executor=tpe)

	worker_thread = threading.Thread(target=itlw.run, daemon=True)
	worker_thread.start()
	time.sleep(1)

@pytest.fixture(scope='package')
def echo_worker(refl_thread):

	itlw = axon.reflector.ITLW(url='localhost', name='echo_worker')

	@axon.worker.rpc(tl=itlw, executor=tpe)
	def echo(msg):
		return msg

	worker_thread = threading.Thread(target=itlw.run, daemon=True)
	worker_thread.start()
	time.sleep(1)

def test_basic_operation(echo_worker, test_service):

	stub = axon.client.get_ServiceStub(f'{axon.config.url_scheme}://localhost:{refl_http_port}/reflected_services')

	test_msg = 'this is a message sent from client to reflector, then to worker, and then back again'
	response = stub.echo_worker.rpc.echo(test_msg).join()
	assert(response == test_msg)

	response = stub.test_service.test_service.print_str(test_msg).join()
	assert(response == 'all done!')

def test_chunking(echo_worker):
	stub = axon.client.get_ServiceStub(f'{axon.config.url_scheme}://localhost:{refl_http_port}/reflected_services')

	# sends a PIL image to and from the worker to test if the chunking feature is working, since the image data should be larger than the max message size in SocketIO
	img = Image.open('./axon/reflector/tests/test_img.png')
	response = stub.echo_worker.rpc.echo(img).join()
	
	diff = ImageChops.difference(img, response)
	assert not diff.getbbox()

@pytest.fixture(scope='package')
def host_worker(refl_thread):

	itlw = axon.reflector.ITLW(url='localhost', name='host_worker')

	@axon.worker.rpc(tl=itlw, executor=tpe)
	def host(service_str, name):
		service = cloudpickle.loads(service_str)
		axon.worker.register_ServiceNode(service, name, tl=itlw)
		itlw.update_profile()
		return 'success'

	worker_thread = threading.Thread(target=itlw.run, daemon=True)
	worker_thread.start()
	time.sleep(1)

def test_hosting(host_worker):
	stub = axon.client.get_ServiceStub(f'{axon.config.url_scheme}://localhost:{refl_http_port}/reflected_services')

	t = DummyClass()
	r = stub.host_worker.rpc.host(cloudpickle.dumps(t), 'hosted_t').join()
	assert(r == 'success')

	stub = axon.client.get_ServiceStub(f'{axon.config.url_scheme}://localhost:{refl_http_port}/reflected_services/host_worker/hosted_t')
	resp = stub.print_str('This comes from the host!').join()
	assert(resp == 'all done!')
	