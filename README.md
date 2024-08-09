# Axon

Axon is a Python framework that enables developers to host services on edge devices and access them over local networks or the Internet. Axon allows developers to deploy services from the edge, utilizing any available devices on hand, rather than using expensive cloud computing and without opening a port on their network. Moreover, calls to services deployed with Axon are made through developer-friendly RPC proxies that match the interface of the variables being served. Axon can expose services quickly and easily, requiring only a few extra lines of code on top of a service’s core logic.

## Installation

`pip install axon-ECRG`

## QuickStart

### Worker

Developers may deploy services by passing Python variables or functions into Axon. These objects are then exposed to distributed access, and clients may create stubs linked to these variables to make calls to them. Designing an Axon service reduces to deciding which functions and variables should be exposed to outside access. Functions can be passed into Axon using the rpc decorator, and variables using the register_ServiceNode function. See below for an example worker script:

```
@axon.worker.rpc()
def print_msg(msg):
print(msg)

l = [1,2,3,4,5]
axon.worker.register_ServiceNode(l, "list_service")

axon.worker.init()
```

### Client

Developers may access services using stub objects created from URLs that identify the service. Parameters are passed into these stubs much like a normal function call. See below for an example client script that accesses the service described above. To access a service hosted by another machine on the same local network or the Internet, 'localhost' must be replaced with the IP address of the desired host machine. 

Functions that are exposed with Axon are called RPCs, and can be accessed with a stub created from a URL with the rpcs endpoint. The stub returned from this call, has attributes corresponding to each RPC that the worker exposes. In this example, the worker exposes a function called 'print_msg', and so the stub created below has a functional attribute with the same name. Calling this attribute on the stub will transmit any arguments passed in to the worker, which will run the RPC on those arguments. After the RPC is invoked the return value will be transmitted back to the client and passed back through the corresponding call to the stub’s attribute. 

The worker script passes the string 'list_service' with the list, and so a stub linked to the list can be created with URLs ending in the same string. Stubs have a matching interface to the remote variable they are linked to, and so the list stub has a pop attribute just like a Python list. Dunder methods like `\_\_get\_item\_\_` are also mimicked on the stub, and so list indexing can be done using the same syntax on the stub as on the list it represents.

```
rpc_stub = axon.client.get_ServiceStub("http://localhost/rpcs")
await rpc_stub.print_msg("Hello World!")

list_stub = axon.client.get_ServiceStub("http://localhost/list_service")
await list_stub.pop() # returns 5
await list_stub[1] # returns 2
```

By default, axon RPC requests return an `AsyncResultHandle` that allows for concurrent code execution during a request with asyncio. The result of the RPC invocation is obtained by calling using the 'await' keyword on the result handle. Another for option when asyncio is impractical is to call `.join()`: 
```
rpc_stub = axon.client.get_ServiceStub("http://localhost/rpcs")
rpc_stub.print_msg("Hello World!").join()

list_stub = axon.client.get_ServiceStub("http://localhost/list_service")
list_stub.pop().join() # returns 5
list_stub[1].join() # returns 2
```

When syncronous behavior is desired, develeopers may pass in a `stub_type` option to make syncronous calls:

```
rpc_stub = axon.client.get_ServiceStub("http://localhost/rpcs", stub_type=axon.stubs.SyncStub)
rpc_stub.print_msg("Hello World!")

list_stub = axon.client.get_ServiceStub("http://localhost/list_service", stub_type=axon.stubs.SyncStub)
list_stub.pop() # returns 5
list_stub[1] # returns 2
```

## Edge Hosting Capability

Axon allows developers to host services on local devices while exposing them to access from anywhere in the world. Normally, local networks block incoming TCP connection requests, keeping user devices safe from the threats of the public internet. Anyone wishing to offer worldwide access to a service on a local device would need to open a port on their router; a significant security consideration. Axon workers may take service requests through a pre-established connection to a trusted third party on the internet, known as a reflector. The reflector would then take requests from clients on the worker's behalf, and pass them down to the worker through this connection.

![](http://143.198.32.69/header.jpg)