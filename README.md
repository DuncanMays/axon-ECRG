# Axon

Axon is a general-purpose RPC-proxy framework developed to facilitate machine learning research at Queen’s University in Kingston, Ontario. It focusses on fast development, being easy-to-use, and it does its best to stay out of the programmer’s way. One of Axon's goals is to make programming distributed systems as similar as possible to programming code that only runs locally. Axon does this by creating distributed equivalents of familiar concepts, such as functions and classes.

## Installation

`pip install axon-ECRG`

## QuickStart

### Worker

Expose a function to distributed access with the `rpc` decorator:

```
from axon import worker

@worker.rpc()
def hello_world():
	print("hello")
	return "world"

worker.init()
```

### Client

RPCs can be called with `RemoteWorker` objects:

```
from axon import client

hw_worker = client.get_RemoteWorker('localhost')

result = hw_worker.rpcs.hello_world().join()

print(result)
```

Replace 'localhost' with the IP address of the remote host, and you can call functions on other computers on your network.

## Asyncio

Axon RPC requests return an `AsyncResultHandle` that allows for concurrent code execution during a request and parallel execution of requests. The result of the RPC invocation is obtained by calling `.join()` on the handle, for example:

```
from axon import client

hw_worker = client.get_RemoteWorker('localhost')

result = hw_worker.rpcs.hello_world()

print("Hi there!")

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

With axon you can expose instances of classes, not just functions, to remote access. Use register_ServiceNode to serve object instances:

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

The same configuration options like `stub_type` can be used in `get_ServiceStub`. Services can be connected with a RemoteWorker object just like RPCs, though they're on an attribute matching the string passed to the `register_ServiceNode` call on worker:

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

It can be a logistical challenge to keep track of the IP addresses of the workers on your network. Fortunetely this problem can be solved with a simple service, the `SignUpService`:

```
from axon import worker

class SignUpService():
    def __init__(self):
            self.ips = []

    def sign_in(self, ip):
            self.ips.append(ip)

    def sign_out(self, ip):
            self.ips.remove(ip)

    def get_ips(self):
            return self.ips

s = SignUpService()
worker.register_ServiceNode(s, 'SignUpService')
worker.init()
```

The idea is that the SignUpService runs at a known IP address, say '192.168.2.10', that way workers are aware of. Then each worker will sign in on startup so that clients can get their IP addresses. 

```
import axon

s = axon.client.get_ServiceStub('192.168.2.19', endpoint_prefix='SignUpService')
self_ip = axon.utils.get_self_ip()
s.sign_in(self_ip).join()

@axon.worker.rpc()
def print_msg(msg):
	print(msg)

axon.worker.init()
```

This has the advantage that both workers and clients only need to know one IP address, yet can discover eachother's IPs and communicate. Clients can obtain the IP addresses of all workers that have signed in:

```
import axon

s = axon.client.get_ServiceStub('192.168.2.19', endpoint_prefix='SignUpService')

worker_ips = s.get_ips().join()
```