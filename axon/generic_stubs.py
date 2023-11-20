from .config import comms_config, default_rpc_config
from .transport import call_simplex_rpc_coro, call_simplex_rpc_async, call_simplex_rpc_sync, call_duplex_rpc_coro, call_duplex_rpc_async, call_duplex_rpc_sync

class GenericStub():

	def __init__(self, worker_ip='localhost', rpc_name=None, endpoint_prefix=default_rpc_config['endpoint_prefix'], comms_pattern='simplex'):
		self.remote_ip = worker_ip
		self.__name__ = rpc_name
		self.endpoint_prefix = endpoint_prefix
		self.comms_pattern = comms_pattern

	def async_call(self, args, kwargs):
		if not self.check_capability():
			raise(BaseException('stub not initialized'))

		url = 'http://'+str(self.remote_ip)+':'+str(comms_config.worker_port)+'/'+self.endpoint_prefix+self.__name__
		
		result = None

		if (self.comms_pattern == 'simplex'):
			result = call_simplex_rpc_async(url, args, kwargs)
		elif (self.comms_pattern == 'duplex'):
			result = call_duplex_rpc_async(url, args, kwargs)
		else:
			raise BaseException('unrecognized comms_pattern')

		return result

	async def coro_call(self, args, kwargs):
		if not self.check_capability():
			raise(BaseException('stub not initialized'))

		url = 'http://'+str(self.remote_ip)+':'+str(comms_config.worker_port)+'/'+self.endpoint_prefix+self.__name__

		result = None
		if (self.comms_pattern == 'simplex'):
			result = await call_simplex_rpc_coro(url, args, kwargs)
		elif (self.comms_pattern == 'duplex'):
			result = await call_duplex_rpc_coro(url, args, kwargs)
		else:
			raise BaseException('unrecognized comms_pattern')

		return result

	def sync_call(self, args, kwargs):
		if not self.check_capability():
			raise(BaseException('stub not initialized'))

		url = 'http://'+str(self.remote_ip)+':'+str(comms_config.worker_port)+'/'+self.endpoint_prefix+self.__name__

		result = None

		if (self.comms_pattern == 'simplex'):
			result = call_simplex_rpc_sync(url, args, kwargs)
		elif (self.comms_pattern == 'duplex'):
			result = call_duplex_rpc_sync(url, args, kwargs)
		else:
			raise BaseException('unrecognized comms_pattern')

		return result

	# returns a boolean indicating if the stub has all the information it needs to make calls or not
	def check_capability(self):
		if (self.__name__ == None):
			return False

		else:
			return True

class AsyncStub(GenericStub):

	def __init__(self, **kwargs):
		GenericStub.__init__(self, **kwargs)

	def __call__(self, *args, **kwargs):
		return self.async_call(args, kwargs)

class CoroStub(GenericStub):

	def __init__(self, **kwargs):
		GenericStub.__init__(self, **kwargs)

	async def __call__(self, *args, **kwargs):
		return await self.coro_call(args, kwargs)

class SyncStub(GenericStub):

	def __init__(self, **kwargs):
		GenericStub.__init__(self, **kwargs)

	def __call__(self, *args, **kwargs):
		return self.sync_call(args, kwargs)