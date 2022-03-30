import sys
sys.path.append('..')

import axon
import asyncio
import torch

tensor = torch.randn([2,2])

async def main():
	
	remote_module = axon.client.ServiceStub('localhost', endpoint_prefix='tensor_service')

	# print(dir(tensor))
	# print(dir(remote_module))

	print(tensor.__class__())
	print(remote_module.__class__)


if (__name__ == '__main__'):
	asyncio.run(main())