import sys
import asyncio
import torch
import uuid

from torch_module_service_worker import TwoNN, FnService
from tqdm import tqdm

sys.path.append('..')
import axon


class FnStub(torch.autograd.Function):

	@staticmethod
	def forward(ctx, expert_handle, x):

		# if the context already has an ID, that means it's been through a FnStub already
		# this could be a problem for recursive patterns, in that case, the stub's context store will need to be a dict of lists of contexts
		if not hasattr(ctx, 'id'):
			ctx.id = uuid.uuid4()

		ctx.backward_handle = expert_handle	

		return expert_handle.apply_expert.___call___.sync_call((ctx.id, x, ), {})

	@staticmethod
	def backward(ctx, g):
		return None, ctx.backward_handle.apply_gradients.___call___.sync_call((ctx.id, g, ), {})

class Remote_Expert(torch.nn.Module):

	def __init__(self, expert_ip, expert_name):
		super(Remote_Expert, self).__init__()

		self.ip = expert_ip
		self.handle = axon.client.ServiceStub(expert_ip, endpoint_prefix=expert_name)

	def forward(self, x):
		return FnStub.apply(self.handle, x)

async def main():

	input_tensor = torch.randn([32, 600], dtype=torch.float32, requires_grad=True).to('cuda:0')
	output_tensor = torch.zeros([32, 100], dtype=torch.float32).to('cuda:0')

	expert_module_1 = Remote_Expert('192.168.2.209', 'expert_service')
	expert_module_2 = Remote_Expert('192.168.2.210', 'expert_service')
	expert_module_3 = Remote_Expert('192.168.2.222', 'expert_service')

	print('configuring experts')
	configure_coros = []
	configure_coros.append(expert_module_1.handle.reset_expert(600))
	configure_coros.append(expert_module_1.handle.set_device('cuda:0'))
	configure_coros.append(expert_module_2.handle.reset_expert(400))
	configure_coros.append(expert_module_2.handle.set_device('cuda:0'))
	configure_coros.append(expert_module_3.handle.reset_expert(200))
	configure_coros.append(expert_module_3.handle.set_device('cuda:0'))
	await asyncio.gather(*configure_coros)

	layer_1 = torch.nn.Linear(600, 400).to('cuda:0')
	layer_2 = torch.nn.Linear(400, 200).to('cuda:0')
	layer_3 = torch.nn.Linear(200, 100).to('cuda:0')

	criteria = torch.nn.MSELoss()

	print('training')
	for i in tqdm(range(100)):

		x = expert_module_1.forward(input_tensor)
		x = layer_1(x)
		x = expert_module_2.forward(x)
		x = layer_2(x)
		x = expert_module_3.forward(x)
		y_hat = layer_3(x)

		loss = criteria(y_hat, output_tensor)

		if (i%10 == 1):
			print(loss.item())
		
		loss.backward()

		await expert_module_1.handle.step()
		await expert_module_2.handle.step()
		await expert_module_3.handle.step()

if (__name__ == '__main__'):
	asyncio.run(main())
