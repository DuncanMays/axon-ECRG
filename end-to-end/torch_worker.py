import sys
sys.path.append('..')

import axon
import torch

class TestClass(torch.nn.Module):

	def __init__(self):
		torch.nn.Module.__init__(self)		

		self.name = 'Duncan'
		self.age = 25
		self.height = 3/12+6

a = TestClass()

# axon.worker.expose_service(a, 'torch_module')
axon.worker.ServiceNode(a, 'torch_module')

if (__name__ == '__main__'):
	axon.worker.init()