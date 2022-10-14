import sys
sys.path.append('..')

import axon
import torch

class TwoNN(torch.nn.Module):

	def __init__(self):
		super(TwoNN, self).__init__()
		
		self.fc1 = torch.nn.Linear(784, 200)
		self.fc2 = torch.nn.Linear(200, 200)
		self.fc3 = torch.nn.Linear(200, 10)

	def forward(self, x):
		
		x = torch.nn.functional.relu(self.fc1(x))
		x = torch.nn.functional.relu(self.fc2(x))
		x = torch.nn.functional.softmax(self.fc3(x), dim=1)

		return x

class FnService():

	def __init__(self, net):
		self.net = net
		self.saved_tensors = None

	def apply(self, x):
		print('apply')

		with torch.enable_grad():
			y = self.net(x)

		self.saved_tensors = (x, y)

		return y.clone()

	def apply_gradients(self, g):
		print('apply_gradients')
		(x, y) = self.saved_tensors
		y.backward(g)
		return x.grad

tensor = torch.randn([2,2])
module = TwoNN()
module_service = FnService(module)
optimizer = torch.optim.Adam([{'params': module.parameters()}], lr=0.0001)

p = next(module.parameters())
@axon.worker.rpc()
def print_grad():
	print(p.grad)

if (__name__ == '__main__'):

	# axon.worker.ServiceNode(tensor, 'tensor_service')
	axon.worker.ServiceNode(module_service, 'module_service', depth=1)
	axon.worker.ServiceNode(optimizer, 'optimizer_service')

	print('initializing worker')
	axon.worker.init()