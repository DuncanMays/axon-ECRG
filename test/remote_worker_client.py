import sys
sys.path.append('..')

import asyncio
from axon import client

remote_worker = client.RemoteWorker('127.0.0.1')

async def main():
	futures = []
	for i in range(10):
		futures.append(remote_worker.rpcs.wait(i))

	await asyncio.gather(*futures)

asyncio.run(main())