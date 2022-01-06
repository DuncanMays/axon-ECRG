# Axon

Edge computing framework developed and maintained by the Edge Computing Research Group at Queen's University

## Installation

`pip install axon-ECRG`

## QuickStart

### Client

`import asyncio\n`
`from axon import client\n`

`hello_world = client.get_simplex_rpc_stub("127.0.0.1", "hello_world")\n`

`async def main():\n`
	`result = await hello_world()\n`
	`print(result)\n`

`asyncio.run(main())\n`

### Worker

`from axon import worker\n`

`@worker.rpc()\n`
`def hello_world():\n`
	`print("hello")\n`
	`return "world"\n`

`worker.init()\n`

Replace '127.0.0.1' with the IP address of the worker, and you can call functions on other computers on your network.