import sys
sys.path.append('..')

import asyncio
from axon import client

hello_world = client.get_simplex_rpc_stub('127.0.0.1', 'hello_world')

async def main():
	result = await hello_world()
	print(result)

asyncio.run(main())