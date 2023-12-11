# Axon

A general-purpose RPC-proxy framework developed to facilitate machine learning research at Queen’s University in Kingston, Ontario. It focusses on fast development, being easy-to-use, and it does its best to not get in the programmer’s way. One of Axon's goals is to make programming distributed systems as similar as possible to programming code that only runs locally. Axon does this by creating distributed equivalents of familiar concepts, such as functions and classes.

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
from axon import client

hw_worker = client.get_RemoteWorker('localhost')

result = hw_worker.rpcs.hello_world().join()

print(result)
```

Replace 'localhost' with the IP address of the worker, and you can call functions on other computers on your network.

## Asyncio

Axon RPC requests return an `AsyncResultHandle` that allow for concurrent code execution during a request and parallel execution of requests. The result of the call is obtained by calling `.join()`, for example:

```
from axon import client

hw_worker = client.get_RemoteWorker('localhost')

result = hw_worker.rpcs.hello_world()

print("Don't forget to drink your ovalmaltine!"")

print(result.join())
```

The `AsyncResultHandle` class can also be awaited using asyncio! Import asyncio and run axon requests inside coroutines using async/await syntax:

```
from axon import client
import asyncio

async def main():
	hw_worker = client.get_RemoteWorker('localhost')
	result = await hw_worker.rpcs.hello_world()
	print(result)

asyncio.run(main())
```

## Synchronous Stubs

If concurrency is not necessary, you may also request axon RPCs synchronously by passing in a different stub type:

```
import axon

hw_worker = axon.client.get_RemoteWorker('localhost', stub_type=axon.stubs.SyncStub)

result = hw_worker.rpcs.hello_world()

print(result)
```

## Services

Axon allows developers to expose instances of classes, not just functions, to remote access. Use register_ServiceNode to serve object instances:

```
from axon import worker

class TestClass():

	def print_msg(self, msg):
		print(msg)

worker.register_ServiceNode(TestClass(), 'test_service')
worker.init()
```

And then call services with:

```
from axon import client

stub = client.get_ServiceStub('localhost', endpoint_prefix='test_service')

stub.print_msg('hello!').join()
```

RPCs are also just a service:

```
from axon import client

stub = client.get_ServiceStub('localhost', endpoint_prefix='rpc')

print(stub.hello_world().join())
```

Services can be connected with a RemoteWorker object just like RPCs:

```
from axon import client

hw_worker = client.get_RemoteWorker('localhost')

result = hw_worker.test_service.print_msg().join()
```

## Error Propegation

Errors in the worker propagate back to the client that invoke the error, and are thrown at the line making the RPC call. For example, a worker that throws:

```
from axon import worker

@worker.rpc()
def raise_error():
	raise BaseException('your code sucks!!!')

worker.init()
```

Would result in the following error message in client:

```
the following error occured in worker:
Traceback (most recent call last):
  File "/home/axon/worker.py", line 77, in invoke_RPC
    result = target_fn(*args, **kwargs)
  File "<stdin>", line 2, in raise_error
BaseException: your code sucks!!!

Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/home/axon/transport_client.py", line 40, in join
    self.value = self.future.result()
  File "/home/python3.8/concurrent/futures/_base.py", line 439, in result
    return self.__get_result()
  File "/home/python3.8/concurrent/futures/_base.py", line 388, in __get_result
    raise self._exception
  File "/home/python3.8/concurrent/futures/thread.py", line 57, in run
    result = self.fn(*self.args, **self.kwargs)
  File "/home/axon/transport_client.py", line 74, in call_rpc_helper
    return error_handler(return_obj)
  File "/home/axon/transport_client.py", line 20, in error_handler
    raise(error)
BaseException: your code sucks!!!
```

## Worker Discovery

How do I find workers on my network? It can be a logistical challenge to keep track of the IP addresses of the workers on your network. To help with this task, axon comes with a discovery module that can be used to discover workers and other entities. If I had two workers on my network I could find their IP addresses you running the following command in a python terminal:

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