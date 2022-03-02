from .utils import serialize, deserialize, GET, POST, async_GET, async_POST
from .config import comms_config, default_rpc_config
from .return_value_linker import ReturnEvent_async, ReturnEvent_coro, RVL
from .simplex_stubs import error_handler, AsyncCallHandle, GenericSimplexStub

import threading
import asyncio
import uuid

# the Return Value Linker is an app that runs in a separate thread and listens for incomming HTTP requests carrying the results from duplex RPC calls
rvl = RVL()

# this function checks to see if the RVL ap is running, and if not, starts it
def ensure_rvl_app():
	global rvl

	if not rvl.running:
		rvl.start_app()

# this function ensures the RVL is active and listening for the return value and then makes a calling request to a duplex RPC
def call_duplex_rpc_async(url, args, kwargs):
	global rvl

	# checks that the RVL is active, and if not, starts one
	ensure_rvl_app()

	return_event = ReturnEvent_async()

	def thread_fn(return_event):
		# we must register an event listenner with the return value linker, which will wait for the incomming result request
		# this uuid will identify the call, so the RVL can lookup the event
		call_id = uuid.uuid4()
		rvl.register(call_id, return_event)

		# this object holds information about the function call that the worker will need to provide to the rvl upon completion
		call_info = {'id': call_id, 'rvl_port': rvl.port}

		# makes the calling request
		status, text = POST(url=url , data={'msg': serialize((call_info, args, kwargs))})
		return_obj = deserialize(text)

		# raises exception if the receiving RPC is simplex, not duplex
		if (return_obj != 'duplex'):
			print(return_obj)
			raise(BaseException('duplex call sent to simplex RPC'))

	request_thread = threading.Thread(target=thread_fn, args=(return_event, ), name='call_duplex_rpc_async.request_thread')
	request_thread.start()

	return AsyncCallHandle(return_event)

# this function ensures the RVL is active and listening for the return value and then makes a calling request to a duplex RPC
async def call_duplex_rpc_coro(url, args, kwargs):
	global rvl
	
	ensure_rvl_app()

	# we must register an event listenner with the return value linker, which will wait for the incomming result request
	# this uuid will identify the call, so the RVL can lookup the event
	call_id = uuid.uuid4()
	return_event = ReturnEvent_coro()
	await return_event.init()
	rvl.register(call_id, return_event)

	# this object holds information about the function call that the worker will need to provide to the rvl upon completion
	call_info = {'id': call_id, 'rvl_port': rvl.port}

	# makes the calling request
	status, text = await async_POST(url=url , data={'msg': serialize((call_info, args, kwargs))})
	return_obj = deserialize(text)

	# raises exception if the receiving RPC is simplex, not duplex
	if (return_obj != 'duplex'):
		print(return_obj)
		raise(BaseException('duplex call sent to simplex RPC'))

	# we now wait for the result to return
	serialized_result = await return_event.get_return_value()

	# deserializes result
	result = deserialize(serialized_result)

	# detects if an error was thrown in worker
	return error_handler(result)

# this function ensures the RVL is active and listening for the return value and then makes a calling request to a duplex RPC
def call_duplex_rpc_sync(url, args, kwargs):
	global rvl
	
	ensure_rvl_app()

	# we must register an event listenner with the return value linker, which will wait for the incomming result request
	# this uuid will identify the call, so the RVL can lookup the event
	call_id = uuid.uuid4()
	return_event = ReturnEvent_async()
	rvl.register(call_id, return_event)

	# this object holds information about the function call that the worker will need to provide to the rvl upon completion
	call_info = {'id': call_id, 'rvl_port': rvl.port}

	# makes the calling request
	status, text = POST(url=url , data={'msg': serialize((call_info, args, kwargs))})
	return_obj = deserialize(text)

	# raises exception if the receiving RPC is simplex, not duplex
	if (return_obj != 'duplex'):
		print(return_obj)
		raise(BaseException('duplex call sent to simplex RPC'))

	# we now wait for the result to return
	serialized_result = return_event.get_return_value()

	# deserializes result
	result = deserialize(serialized_result)

	# detects if an error was thrown in worker
	return error_handler(result)

class GenericDuplexStub(GenericSimplexStub):

	def __init__(self, *args, **kwargs):
		GenericSimplexStub.__init__(self, *args, **kwargs)

	def async_call(self, args, kwargs):
		if not self.check_capability():
			raise(BaseException('stub not initialized'))

		url = 'http://'+str(self.remote_ip)+':'+str(comms_config.worker_port)+'/'+self.endpoint_prefix+self.__name__
		
		return call_duplex_rpc_async(url, args, kwargs)

	async def coro_call(self, args, kwargs):
		if not self.check_capability():
			raise(BaseException('stub not initialized'))

		url = 'http://'+str(self.remote_ip)+':'+str(comms_config.worker_port)+'/'+self.endpoint_prefix+self.__name__

		return await call_duplex_rpc_coro(url, args, kwargs)

	def sync_call(self, args, kwargs):
		if not self.check_capability():
			raise(BaseException('stub not initialized'))

		url = 'http://'+str(self.remote_ip)+':'+str(comms_config.worker_port)+'/'+self.endpoint_prefix+self.__name__

		return call_duplex_rpc_sync(url, args, kwargs)

class SyncDuplexStub(GenericDuplexStub):

	def __init__(self, worker_ip='localhost', rpc_name=None):
		GenericSimplexStub.__init__(self, worker_ip=worker_ip, rpc_name=rpc_name)

	def __call__(self, *args, **kwargs):
		return self.sync_call(args, kwargs)

class AsyncDuplexStub(GenericDuplexStub):

	def __init__(self, worker_ip='localhost', rpc_name=None):
		GenericSimplexStub.__init__(self, worker_ip=worker_ip, rpc_name=rpc_name)

	def __call__(self, *args, **kwargs):
		return self.async_call(args, kwargs)

class CoroDuplexStub(GenericDuplexStub):

	def __init__(self, worker_ip='localhost', rpc_name=None):
		GenericSimplexStub.__init__(self, worker_ip=worker_ip, rpc_name=rpc_name)

	async def __call__(self, *args, **kwargs):
		return await self.coro_call(args, kwargs)