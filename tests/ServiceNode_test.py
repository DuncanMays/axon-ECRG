from sys import path
path.append('..')

import axon
import time
import pytest

import threading

class DummyClass():

	def __init__(self, depth=3):
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

	print('test_add_child_child_config passed!')

def test_remove_child_not_live():

	t = DummyClass()
	s = axon.worker.ServiceNode(t, 'test')

	s.remove_child('test_fn')

	# checks that the ServiceNode no longer has a child called test_fn
	assert('test_fn' not in s.children)

	# checks that the necessary RPCs have been removed from the transport layer
	assert('/test/test_fn' not in s.tl.rpcs)
	assert('/test/test_fn/__call__' not in s.tl.rpcs)

# def test_add_child_live():

# 	port = axon.utils.get_open_port(lower_bound=8003)
# 	tlw = axon.worker.HTTPTransportWorker(port)

# 	t = DummyClass()
# 	s = axon.worker.ServiceNode(t, 'test', tl=tlw)

# 	def test_add_child_rpc(self):
# 		print('test_add_child_rpc called')

# 	print(port)

# 	worker_thread = threading.Thread(target=axon.worker.init(), daemon=True)
# 	worker_thread.start()
# 	time.sleep(1)

# 	# stub = axon.client.get_ServiceStub(f'http://localhost:{port}/test')

# 	# print(dir(stub))

# 	# s.add_child('test_add_child', test_add_child_rpc)