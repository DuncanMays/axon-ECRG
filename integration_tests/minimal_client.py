import sys
sys.path.append('..')

from axon import client
import asyncio

stub = client.RemoteWorker('localhost')

async def main():
	result = await stub.rpcs.print_return('hello', 'world')
	print(result)

asyncio.run(main())
