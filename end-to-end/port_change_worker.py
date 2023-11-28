import sys
sys.path.append('..')
import axon

class TestClass():
	def hello(self):
		print('hi there!')

@axon.worker.rpc()
def print_str(s):
	print(s)

t = TestClass()
axon.worker.register_ServiceNode(t, name='test')

axon.worker.init(port=5000)