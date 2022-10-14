import sys
import asyncio
import torch

from torch_module_service_worker import TwoNN, FnService
from tqdm import tqdm

sys.path.append('..')
import axon

input_tensor = torch.randn([32, 784], dtype=torch.float32, requires_grad=True)
output_tensor = torch.zeros([32, 10], dtype=torch.float32)
output_tensor[:, 0] = 1

criteria = torch.nn.CrossEntropyLoss()

service_handle = axon.client.ServiceStub('localhost', endpoint_prefix='module_service')
# service_handle = FnService(TwoNN())

class FnStub(torch.autograd.Function):

	def __init__(self):
		super().__init__()

	@staticmethod
	def forward(ctx, x):
		return service_handle.apply.___call___.sync_call((x, ), {})


	@staticmethod
	def backward(ctx, g):
		return service_handle.apply_gradients.___call___.sync_call((g, ), {})


async def main():

	rpcs = axon.client.RemoteWorker('localhost').rpcs
	remote_nn = FnStub()
	remote_optim = axon.client.ServiceStub('localhost', endpoint_prefix='optimizer_service')

	# remote_nn = local_nn
	# remote_optim = local_optim


	for i in tqdm(range(100)):
		y_hat = remote_nn.apply(input_tensor)

		loss = criteria(y_hat, output_tensor)

		print(loss.item())
		
		await remote_optim.zero_grad()
		loss.backward()
		await remote_optim.step()



if (__name__ == '__main__'):
	asyncio.run(main())