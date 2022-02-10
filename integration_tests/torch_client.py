import sys
sys.path.append('..')

import axon
import torch
import asyncio

async def main():

	w = axon.client.RemoteWorker('localhost')

	print(dir(w.rpcs))

asyncio.run(main())