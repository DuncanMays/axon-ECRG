# this file starts a thread with an axon worker in it, for the purposes of testing client code

import threading
import axon

@axon.worker.rpc(comms_pattern='simplex')
def simplex_rpc(prefix, suffix='simplex test failed'):
	return prefix+suffix

@axon.worker.rpc(comms_pattern='duplex')
def duplex_rpc(prefix, suffix='duplex test failed'):
	return prefix+suffix

class TestClass():
	def __init__(self, depth=1):
		self.depth = depth

		if (depth>1):
			self.child = TestClass(depth=self.depth-1)
		else:
			self.child = None

	def test_fn(self):
		print(f'test_fn called at depth {self.depth}')

	def __call__(self):
		print(f'__call__ called at depth {self.depth}')

# the endpoint that our service will be located at
endpoint = 'test_endpoint_prefix/'

# defines an instance of TestClass and creates a service node out of it
test_service_depth = 3
t_simplex = TestClass(depth=test_service_depth)
t_duplex = TestClass(depth=test_service_depth)

simplex_service = axon.worker.register_ServiceNode(t_simplex, 'simplex_service', depth=test_service_depth, endpoint_prefix=endpoint)
duplex_service = axon.worker.register_ServiceNode(t_duplex, 'duplex_service', depth=test_service_depth, endpoint_prefix=endpoint, comms_pattern='duplex')

worker_thread = threading.Thread(target=axon.worker.init, daemon=True, name='axon/tests/__init__.py')
worker_thread.start()