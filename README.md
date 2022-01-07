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

The function `get_simplex_rpc_stub` returns an RPC stub that calls the function `hello_world` on "127.0.0.1" with a single HTTP request. This could become a problem when the function being called might take longer than the timeout of an HTTP request. If the function calls other RPCs and stacks latencies, or performs a stateful operation on the worker that requires the aqcisition of a threadlock, the calling HTTP could timeout and crash.

The solution then, is to use a separate HTTP request to return the result to the caller of the function. This pattern is called a duplex RPC, and can be performed with simple alterations:

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

The reccommended way of calling RPCs is through a RemoteWorker object. This will automatically distinguish between simplex and duplex RPCs, without any involvement from the caller. RemoteWorkers can be instantiated with the IP address of the worker they are associated with, and are meant to be a local represenation of that worker.

### Client

```
import asyncio
from axon import client

remote_worker = client.RemoteWorker('127.0.0.1')

async def main():
	result = await remote_worker.rpcs.fn_1('hello')
	print(result)

	result = await remote_worker.rpcs.fn_2('world')
	print(result)

asyncio.run(main())
```

### Worker

```
from axon import worker

@worker.rpc()
def fn_1(a):
	print(a)
	return 'this is simplex_fn'

@worker.rpc(comms_pattern='duplex')
def fn_2(a):
	print(a)
	return 'this is duplex_fn'

worker.init()
```

#### How do I find workers on my network?

It can be a logistical challenge to keep track of the IP addresses of the workers on your network. To help with this task, axon comes with a discovery module that can be used to discover workers and other entities. If I had two workers on my network I could find their IP addresses you running the following command in a python terminal:

`axon.discovery.broadcast_discovery(num_hosts=2, timeout=3)`

This would return the following array of IP addresses:

`['192.168.2.19', '192.168.2.26']`

The function `broadcast_discovery` will search for axon entities that are listenning on the default port, and will return a list of the IP addresses of all the entities it finds. By default it spends 10 seconds searching, but this can be set with the timeout option. If you know how many workers are on your network, you can tell axon to stop looking after it finds a certain number of hosts with the num_hosts option, saving the time it takes to wait for the timeout.

RPCs can also be run in their own thread or a Process by passing `executor='Thread'` or `executor='Process'` to the rcp decorator. Be warned that this feature is on the chopping block, to be replaced by literal `ThreadPool` or `ProcessPool` executors rather than threads and processes instantiated per call.
