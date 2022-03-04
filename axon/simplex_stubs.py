from .utils import serialize, deserialize, GET, POST, async_GET, async_POST
from .config import comms_config, default_rpc_config
from .return_value_linker import ReturnEvent_async

import threading

# this function checks if an error flag has been set and raises the corresponding error if it has
def error_handler(return_obj):
	if (return_obj['errcode'] == 1):
		# an error occured in worker, raise it
		(error_info, error) = return_obj['result']

		print('the following error occured in worker:')
		print(error_info)
		raise(error)

	else:
		# returns the result
		return return_obj['result']

# this function makes a calling request to a simplex RPC
async def call_simplex_rpc_coro(url, args, kwargs):
	
	# makes the calling request
	status, text = await async_POST(url=url , data={'msg': serialize((args, kwargs))})

	if (text =='duplex'):
		raise(BaseException('simplex call sent to duplex RPC'))

	# deserializes return object from worker
	return_obj = deserialize(text)
	return error_handler(return_obj)

class AsyncCallHandle():

	def __init__(self, response_event):
		self.response_event = response_event

	def join(self):
		text = self.response_event.get_return_value()

		if (text =='duplex'):
			raise(BaseException('simplex call sent to duplex RPC'))

		# deserializes return object from worker
		return_obj = deserialize(text)
		return error_handler(return_obj)

# this function makes a calling request to a simplex RPC, and returns a handle which will block and return the result of the request on .join
def call_simplex_rpc_async(url, args, kwargs):

	response_event = ReturnEvent_async()
	
	def thread_fn(response_event):
		# makes the calling request
		status, text = POST(url=url , data={'msg': serialize((args, kwargs))})
		response_event.put_return_value(text)

	request_thread = threading.Thread(target=thread_fn, args=(response_event, ), name='call_duplex_rpc_async.request_thread')
	request_thread.start()

	return AsyncCallHandle(response_event)

# this function makes a calling request to a simplex RPC
def call_simplex_rpc_sync(url, args, kwargs):
	status, text = POST(url=url , data={'msg': serialize((args, kwargs))})
	
	if (text =='duplex'):
		raise(BaseException('simplex call sent to duplex RPC'))

	# deserializes return object from worker
	return_obj = deserialize(text)
	return error_handler(return_obj)

class GenericSimplexStub:

	def __init__(self, worker_ip='localhost', rpc_name=None, endpoint_prefix=default_rpc_config['endpoint_prefix']):
		self.remote_ip = worker_ip
		self.__name__ = rpc_name
		self.endpoint_prefix = endpoint_prefix

	def async_call(self, args, kwargs):
		if not self.check_capability():
			raise(BaseException('stub not initialized'))

		url = 'http://'+str(self.remote_ip)+':'+str(comms_config.worker_port)+'/'+self.endpoint_prefix+self.__name__
		
		return call_simplex_rpc_async(url, args, kwargs)

	async def coro_call(self, args, kwargs):
		if not self.check_capability():
			raise(BaseException('stub not initialized'))

		url = 'http://'+str(self.remote_ip)+':'+str(comms_config.worker_port)+'/'+self.endpoint_prefix+self.__name__

		return await call_simplex_rpc_coro(url, args, kwargs)

	def sync_call(self, args, kwargs):
		if not self.check_capability():
			raise(BaseException('stub not initialized'))

		url = 'http://'+str(self.remote_ip)+':'+str(comms_config.worker_port)+'/'+self.endpoint_prefix+self.__name__

		return call_simplex_rpc_sync(url, args, kwargs)

	# returns a boolean indicating if the stub has all the information it needs to make calls or not
	def check_capability(self):
		if (self.__name__ == None):
			return False

		else:
			return True

class AsyncSimplexStub(GenericSimplexStub):

	def __init__(self, **kwargs):
		GenericSimplexStub.__init__(self, **kwargs)

	def __call__(self, *args, **kwargs):
		return self.async_call(args, kwargs)

class CoroSimplexStub(GenericSimplexStub):

	def __init__(self, **kwargs):
		GenericSimplexStub.__init__(self, **kwargs)

	async def __call__(self, *args, **kwargs):
		return await self.coro_call(args, kwargs)

class SyncSimplexStub(GenericSimplexStub):

	def __init__(self, **kwargs):
		GenericSimplexStub.__init__(self, **kwargs)

	def __call__(self, *args, **kwargs):
		return self.sync_call(args, kwargs)