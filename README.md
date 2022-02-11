# Axon

Edge computing framework developed and maintained by the Edge Computing Research Group at Queen's University.

## Installation

`pip install axon-ECRG`

## QuickStart

### Worker

```
from axon import worker

@worker.rpc()
def hello_world():
	print("hello")
	return "world"

worker.init()
```

### Client

```
import asyncio
import axon

hello_world = axon.simplex_stubs.SyncSimplexStub(worker_ip='localhost', rpc_name='hello_world')

result = hello_world()

print(result)
```

Replace '127.0.0.1' with the IP address of the worker, and you can call functions on other computers on your network.

#### What does simplex mean?

The call to `SyncSimplexStub` returns an RPC stub that calls the function `hello_world` on "127.0.0.1" with a single HTTP request. This could become a problem when the function being called might take longer than the timeout of an HTTP request. If the function calls other RPCs and stacks latencies, or performs a stateful operation on the worker that requires the aqcisition of a threadlock, the calling HTTP could timeout and crash.

The solution then, is to use a separate HTTP request to return the result to the caller of the function. This pattern is called a duplex RPC, and can be performed with simple alterations:

### Worker

```
from axon import worker

@worker.rpc(comms_pattern="duplex")
def hello_world():
	print("hello")
	return "world"

worker.init()
```

### Client

```
import asyncio
from axon import client

hello_world = client.get_duplex_rpc_stub("127.0.0.1", "hello_world")

async def main():
	await client.start_client()

	result = await hello_world()
	print(result)

asyncio.run(main())
```

Note that the call to `client.start_client()` is unneccessary but considered a best practice. To receive the incomming HTTP request containing the result of the function being called, the client must be started before the calling request is made. This is done automatically upon the first call to a duplex RPC, and so if not done explicitly it will add to the latency of the first call.

#### What if I don't know if a function is duplex or simplex prior to calling it?

The reccommended way of calling RPCs is through a RemoteWorker object. This will automatically distinguish between simplex and duplex RPCs, without any involvement from the caller. RemoteWorkers can be instantiated with the IP address of the worker they are associated with, and are meant to be a local represenation of that worker.

### Worker

```
from axon import worker

@worker.rpc()
def fn_1(a):
	print(a)
	return 'this is a simplex function'

@worker.rpc(comms_pattern='duplex')
def fn_2(a):
	print(a)
	return 'this is a duplex function'

worker.init()
```

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

RPCs can also be run in their own thread or a Process by passing `executor='Thread'` or `executor='Process'` to the rcp decorator. Be warned that this feature is on the chopping block, to be replaced by literal `ThreadPool` or `ProcessPool` executors rather than threads and processes instantiated per call.

#### How do I find workers on my network?

It can be a logistical challenge to keep track of the IP addresses of the workers on your network. To help with this task, axon comes with a discovery module that can be used to discover workers and other entities. If I had two workers on my network I could find their IP addresses you running the following command in a python terminal:

`axon.discovery.broadcast_discovery(num_hosts=2, timeout=3)`

This would return the following array of IP addresses:

`['192.168.2.19', '192.168.2.26']`

The function `broadcast_discovery` will search for axon entities that are listenning on the default port, and will return a list of the IP addresses of all the entities it finds. By default it spends 10 seconds searching, but this can be set with the timeout option. If you know how many workers are on your network, you can tell axon to stop looking after it finds a certain number of hosts with the num_hosts option, saving the time it takes to wait for the timeout.

Discovering workers via broadcasts is inneficient and causes a lot of network noise. The right way to discover workers is with a notice board, which workers can sign into to show that they're willing to participate in the network, and clients can query to discover the IP adresses of workers. Using a notice board means you only need to remember one IP address, the notice board's, instead of the IP address if every active worker. Starting a notice board is as simple as:

```
import axon

nb = axon.discovery.NoticeBoard()

nb.start()
```

Workers can sign in and out of a notice board with the `sign_in` and `sign_out` functions from the discovery module, and clients can query it for active workers with the `get_ips` function. A helpful function is:

```
import axon, requests

nb_ip = '192.168.2.19'

async def start_up():
	try:
		axon.discovery.sign_in(ip=nb_ip)

	except(requests.exceptions.ConnectionError):
		print('no notice board at:', nb_ip)

		ip_list = await axon.discovery.broadcast_discovery(num_hosts=1, port=axon.config.comms_config.notice_board_port)

		if (len(ip_list) == 0):
			print('no notice board on network, sign in unsuccessful')

		else:
			nb_ip = ip_list.pop()
			print('notice board at a new ip:', nb_ip)
			axon.discovery.sign_in(ip=nb_ip)
```

which will try signing into a notice board at a recorded IP, but in case of failure will look for a notice board on the network, and then either sign into it or give up depending on weather or not it finds one. Notice that the notice board runs on a different port from workers, and so we must specify `port=axon.config.comms_config.notice_board_port` in the call to broadcast_discovery. This is done so that the notice board can run on the same machine as a worker.