# Axon

Edge computing framework developed and maintained by the Edge Computing Research Group at Queen's University

## Installation

pip install axon-ECRG

## QuickStart

### Client

`import asyncio
from axon import client

hello_world = client.get_simplex_rpc_stub("127.0.0.1", "hello_world")

async def main():
	result = await hello_world()
	print(result)

asyncio.run(main())`

### Worker

`from axon import worker

@worker.rpc()
def hello_world():
	print("hello")
	return "world"

worker.init()`

Replace '127.0.0.1' with the IP address of the worker, and you can call functions on other computers on your network.