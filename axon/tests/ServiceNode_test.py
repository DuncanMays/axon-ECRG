import axon
import time
import pytest
import threading
import pickle

default_depth = 3
url_scheme = axon.config.url_scheme
TransportWorker = type(axon.config.default_service_config['tl'])

class DummyClass():

	def __init__(self, depth=default_depth):
		self.child = None
		self.depth = depth

		if (depth>0):
			self.child = DummyClass(depth=depth-1)

	def test_fn(self):
		print('test fn called at depth: '+str(self.depth))
		pass

def test_add_child_not_live():

	t = DummyClass()
	s = axon.worker.ServiceNode(t, 'test')

	def test_add_child_rpc(self):
		print('test_add_child_rpc called')

	s.add_child('test_add_child', test_add_child_rpc)

	# checks that the parent node has test_add_child_rpc as a child
	assert('test_add_child' in s.children)

	# checks that the endpoint prefix is correct
	child_config = s.children['test_add_child'].children['__call__']
	assert(child_config['endpoint_prefix'] == '/test/test_add_child')

	# checks that the ServiceNode's profile contains the added child
	p = s.get_profile()
	assert('test_add_child' in p)

	print('test_add_child_child_config passed!')

def test_remove_child_not_live():

	t = DummyClass()
	s = axon.worker.ServiceNode(t, 'test')

	s.remove_child('test_fn')

	# checks that the ServiceNode no longer has a child called test_fn
	assert('test_fn' not in s.children)

	# checks that the ServiceNode's profile does not contain the added child
	p = s.get_profile()
	assert('test' not in p)

	# checks that the necessary RPCs have been removed from the transport layer
	assert('/test/test_fn' not in s.tl.rpcs)
	assert('/test/test_fn/__call__' not in s.tl.rpcs)

def test_add_child_live():

	port = axon.utils.get_open_port(lower_bound=8003)
	tlw = TransportWorker(port)

	t = DummyClass()
	s = axon.worker.ServiceNode(t, 'test', tl=tlw)

	worker_thread = threading.Thread(target=tlw.run, daemon=True)
	worker_thread.start()
	time.sleep(0.5)

	child = DummyClass()

	s.add_child('test_add_child', child)

	stub = axon.client.get_ServiceStub(f'{url_scheme}://localhost:{port}/test')

	stub.test_add_child.test_fn().join()

def test_remove_child_live():

	port = axon.utils.get_open_port(lower_bound=8004)
	tlw = TransportWorker(port)

	t = DummyClass()
	s = axon.worker.ServiceNode(t, 'test', tl=tlw)

	worker_thread = threading.Thread(target=tlw.run, daemon=True)
	worker_thread.start()
	time.sleep(0.5)

	# the stub before the child gets removed
	stub_with_child = axon.client.get_ServiceStub(f'{url_scheme}://localhost:{port}/test')

	s.remove_child('child')

	# recursively checks that all the child's children were removed as well
	for i in range(default_depth-1):
		print(i)
		stub_with_child = stub_with_child.child

		with pytest.raises(KeyError):
			stub_with_child.test_fn().join()

	# the stub after the child gets removed
	no_child_stub = axon.client.get_ServiceStub(f'{url_scheme}://localhost:{port}/test')

	# checks that the child attribute has been removed from the stub
	assert(not hasattr(no_child_stub, 'child'))