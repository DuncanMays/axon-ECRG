import sys
sys.path.append('..')

import axon
import torch

class Expert(torch.nn.Module):

	def __init__(self, layer_width=200):
		super(Expert, self).__init__()
		
		self.fc1 = torch.nn.Linear(layer_width, layer_width)
		self.fc2 = torch.nn.Linear(layer_width, layer_width)

	def forward(self, x):
		
		x = torch.nn.functional.relu(self.fc1(x))
		x = torch.nn.functional.relu(self.fc2(x))

		return x

class ExpertService():

	def __init__(self):
		self.device = 'cpu'
		self.expert = Expert()
		self.expert.to(self.device)
		self.optimizer = torch.optim.Adam([{'params': self.expert.parameters()}], lr=0.0001)
		self.saved_tensors = {}

	def apply_expert(self, ctx_id, x):
		x = x.to(self.device)

		with torch.enable_grad():
			y = self.expert(x)

		self.saved_tensors[ctx_id] = (x, y)

		return y.clone()

	def apply_gradients(self, ctx_id, g):
		(x, y) = self.saved_tensors[ctx_id]
		del self.saved_tensors[ctx_id]

		x = x.to(self.device)
		y = y.to(self.device)

		y.backward(g)
		return x.grad

	def reset_expert(self, layer_width=200):
		self.expert = Expert(layer_width)
		self.expert.to(self.device)
		self.optimizer = torch.optim.Adam([{'params': self.expert.parameters()}], lr=0.0001)

	def set_device(self, device_name):
		self.expert.to(device_name)
		self.device = device_name

	def step(self):
		# print(next(self.expert.parameters()).grad.mean())
		self.optimizer.step()
		self.optimizer.zero_grad()


expert_service = ExpertService()

if (__name__ == '__main__'):

	axon.worker.ServiceNode(expert_service, 'expert_service', depth=1)

	print('starting worker')
	axon.worker.init()