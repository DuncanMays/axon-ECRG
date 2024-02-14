from sys import path
path.append('..')

import axon
import time

class DummyClass():

	def __init__(self, depth=3):
		self.child = None
		self.depth = depth

		if (depth>0):
			self.child = DummyClass(depth=depth-1)

	def test_fn(self):
		print('test fn called at depth: '+str(self.depth))
		pass

def test_add_child():

	t = DummyClass()
	s = axon.worker.ServiceNode(t, 'test')

	test_config = {
		'executor' : 'dummy_executor',
		'endpoint_prefix' : 'dummy_endpoint',
	}

	def test_add_child_rpc(self):
		print('test_add_child_rpc called')

	s.add_child('test_add_child', test_add_child_rpc, executor='dummy_executor')

	child_config = s.children['test_add_child'].children['__call__']
	assert(child_config['executor'] == 'dummy_executor')

	print('test_add_child_child_config passed!')