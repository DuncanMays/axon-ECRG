from .utils import serialize, deserialize, GET, POST, async_GET, async_POST
from .config import comms_config, default_rpc_config
from .return_value_linker import ReturnEvent_async, RVL

import threading

# URL of RPC
# url = 'http://'+str(worker_ip)+':'+str(comms_config.worker_port)+'/'+default_rpc_config['endpoint_prefix']+rpc_name

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

# this function makes a calling request to a simplex RPC on the worker with IP worker_ip to the RPC named rpc_name
async def call_simplex_rpc_coro(url, args, kwargs):
	
	# makes the calling request
	status, text = await async_POST(url=url , data={'msg': serialize((args, kwargs))})

	if (text =='duplex'):
		raise(BaseException('simplex call sent to duplex RPC'))

	# deserializes return object from worker
	return_obj = deserialize(text)
	return error_handler(return_obj)

class SimplexCallHandle():

	def __init__(self, response_event):
		self.response_event = response_event

	def join(self):
		status, text = self.response_event.get_return_value()

		if (text =='duplex'):
			raise(BaseException('simplex call sent to duplex RPC'))

		# deserializes return object from worker
		return_obj = deserialize(text)
		return error_handler(return_obj)

# this function makes a calling request to a simplex RPC on the worker with IP worker_ip to the RPC named rpc_name
def call_simplex_rpc_async(url, args, kwargs):

	response_event = ReturnEvent_async()
	
	def thread_fn(response_event):
		# makes the calling request
		status, text = POST(url=url , data={'msg': serialize((args, kwargs))})
		response_event.put_return_value((status, text))

	request_thread = threading.Thread(target=thread_fn, args=(response_event, ))
	request_thread.start()

	return SimplexCallHandle(response_event)

class GenericSimplexStub:

	def __init__(self, worker_ip='localhost', rpc_name=None):
		self.remote_ip = worker_ip
		self.__name__ = rpc_name

	def async_call(self, args, kwargs):
		if not self.check_capability():
			raise(BaseException('stub not initialized'))

		url = 'http://'+str(self.remote_ip)+':'+str(comms_config.worker_port)+'/'+default_rpc_config['endpoint_prefix']+self.__name__
		
		return call_simplex_rpc_async(url, args, kwargs)

	async def coro_call(self, args, kwargs):
		if not self.check_capability():
			raise(BaseException('stub not initialized'))

		url = 'http://'+str(self.remote_ip)+':'+str(comms_config.worker_port)+'/'+default_rpc_config['endpoint_prefix']+self.__name__

		return await call_simplex_rpc_coro(url, args, kwargs)

	def sync_call(self, args, kwargs):
		t = self.async_call(args, kwargs)
		return t.join()

	# returns a boolean indicating if the stub has all the information it needs to make calls or not
	def check_capability(self):
		if (self.__name__ == None):
			return False

		else:
			return True

class SyncSimplexStub(GenericSimplexStub):

	def __init__(self, worker_ip='localhost', rpc_name=None):
		GenericSimplexStub.__init__(self, worker_ip=worker_ip, rpc_name=rpc_name)

	def __call__(self, *args, **kwargs):
		return self.sync_call(args, kwargs)

class AsyncSimplexStub(GenericSimplexStub):

	def __init__(self, worker_ip='localhost', rpc_name=None):
		GenericSimplexStub.__init__(self, worker_ip=worker_ip, rpc_name=rpc_name)

	def __call__(self, *args, **kwargs):
		return self.async_call(args, kwargs)

class CoroSimplexStub(GenericSimplexStub):

	def __init__(self, worker_ip='localhost', rpc_name=None):
		GenericSimplexStub.__init__(self, worker_ip=worker_ip, rpc_name=rpc_name)

	async def __call__(self, *args, **kwargs):
		return await self.coro_call(args, kwargs)