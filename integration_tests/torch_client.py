import sys
sys.path.append('..')

import axon
import torch
import asyncio

async def main():

	# w = axon.client.RemoteWorker('localhost')
	w = axon.client.get_MetaStub('localhost', endpoint_prefix='torch_module', stub_type=axon.stubs.SyncSimplexStub)

	print('rpcs' in dir(w))
	print(callable(w))

asyncio.run(main())