# Axon

Edge computing framework developed and maintained by the Edge Computing Research Group at Queen's University.

## Installation

`pip install axon-ECRG`

## QuickStart

### Client

```
import asyncio
from axon import client

hello_world = client.get_simplex_rpc_stub("127.0.0.1", "hello_world")

async def main():
	result = await hello_world()
	print(result)

asyncio.run(main())
```

### Worker

```
from axon import worker

@worker.rpc()
def hello_world():
	print("hello")
	return "world"

worker.init()
```

Replace '127.0.0.1' with the IP address of the worker, and you can call functions on other computers on your network.

#### What does simplex mean?

The function `get_simplex_rpc_stub` returns an RPC stub that calls a function on "127.0.0.1" with a single HTTP request. This could become a problem when the function being called might take longer than the timeout of an HTTP request. If the function calls other RPCs and stacks latencies, or performs a stateful operation on the worker that requires the aqcisition of a threadlock, the calling HTTP could timeout and cause a crash.

The solution then, is to use a separate HTTP request to return the result to the caller of the function. This is a duplex RPC, and can be performed with simple alterations:

### Client

```
import asyncio
from axon import client

hello_world = client.get_duplex_rpc_stub("127.0.0.1", "hello_world")

async def main():
	await client.start()

	result = await hello_world()
	print(result)

asyncio.run(main())
```

### Worker

```
from axon import worker

@worker.rpc(comms_pattern="duplex")
def hello_world():
	print("hello")
	return "world"

worker.init()
```

Note that the call to `client.start()` is unneccessary but considered a best practice. To receive the incomming HTTP request containing the result of the function being called, the client must be started before the calling request is made. This is done automatically upon the first call to a duplex RPC, and so if not done explicitly it will add to the latency of the first call.

#### What if I don't know if a function is duplex or simplex prior to calling it?