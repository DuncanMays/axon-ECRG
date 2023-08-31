from sys import path
path.append('..')

import axon
import time

class TestClass():

	def __init__(self, depth=3):
		self.child = None
		self.depth = depth

		if (depth>0):
			self.child = TestClass(depth=depth-1)

	def test_fn(self):
		print('test fn called at depth: '+str(self.depth))
		pass

def test_add_child_child_config():

	t = TestClass()
	s = axon.worker.ServiceNode(t, 'test')

	def simplex_rpc(self):
		print('simplex_rpc called')

	def duplex_rpc(self):
		print('duplex_rpc called')

	s.add_child('simplex_child', simplex_rpc, comms_pattern='simplex')
	s.add_child('duplex_child', duplex_rpc, comms_pattern='duplex')

	assert(s.children['simplex_child'].children['__call__']['comms_pattern'] == 'simplex')
	assert(s.children['duplex_child'].children['__call__']['comms_pattern'] == 'duplex')

	print('test_add_child_child_config passed!')

def main():
	test_add_child_child_config()

if (__name__=='__main__'):
	main()