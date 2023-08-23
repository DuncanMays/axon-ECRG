import sys
import asyncio
import torch
import uuid

from torch_module_service_worker import TwoNN, FnService
from tqdm import tqdm

sys.path.append('..')
import axon

service_handle = axon.client.ServiceStub('localhost', endpoint_prefix='module_service')
# service_handle = FnService(TwoNN())

class FnStub(torch.autograd.Function):

	def __init__(self):
		super().__init__()

	@staticmethod
	def forward(ctx, x):

		# if the context already has an ID, that means it's been through a FnStub already
		# this could be a problem for recursive patterns, in that case, the stub's context store will need to be a dict of lists of contexts
		if not hasattr(ctx, 'id'):
			ctx.id = uuid.uuid4()	

		return service_handle.apply.___call___.sync_call((ctx.id, x, ), {})


	@staticmethod
	def backward(ctx, g):
		return service_handle.apply_gradients.___call___.sync_call((ctx.id, g, ), {})


async def main():

	rpcs = axon.client.RemoteWorker('localhost').rpcs
	remote_nn = FnStub()
	remote_optim = axon.client.ServiceStub('localhost', endpoint_prefix='optimizer_service')

	# this block tests for gradient crossing
	# it evaluates a remote NN on two tensors A and B, then calls backward on a tensor calculated from A
	# if B has a gradient after ad A doesn't the gradients have been crossed

	A = torch.randn([32, 784], dtype=torch.float32, requires_grad=True)
	B = torch.zeros([32, 784], dtype=torch.float32, requires_grad=True)

	A_hat = remote_nn.apply(A)
	B_hat = remote_nn.apply(B)

	A_sum = torch.sum(A_hat)
	A_sum.backward()

	print(A.grad)
	print(B.grad)

	B_sum = torch.sum(B_hat)
	B_sum.backward()

	print(B.grad)

	# this block tests training a remote ANN with loss calculated locally

	# input_tensor = torch.randn([32, 784], dtype=torch.float32, requires_grad=True)
	# output_tensor = torch.zeros([32, 10], dtype=torch.float32)
	# output_tensor[:, 0] = 1

	# criteria = torch.nn.CrossEntropyLoss()

	# for i in tqdm(range(100)):
	# 	y_hat = remote_nn.apply(input_tensor)

	# 	loss = criteria(y_hat, output_tensor)

	# 	if (i%10 == 0):
	# 		print(loss.item())
		
	# 	await remote_optim.zero_grad()
	# 	loss.backward()
	# 	await remote_optim.step()

if (__name__ == '__main__'):
	asyncio.run(main())