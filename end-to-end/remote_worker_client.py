from sys import path
path.append('..')

import sys
import asyncio
from axon import client

remote_worker = client.RemoteWorker('127.0.0.1')

async def main():
	result = await remote_worker.rpcs.fn_1('hello')
	print(result)

	result = await remote_worker.rpcs.fn_2('world')
	print(result)

asyncio.run(main())