from .config import comms_config, default_rpc_endpoint

class GenericStub():

	def __init__(self, worker_ip='localhost', tl=None, port=comms_config.worker_port, rpc_name=None, endpoint_prefix=default_rpc_endpoint):
		self.remote_ip = worker_ip
		self.tl = tl
		self.port = port
		self.__name__ = rpc_name
		self.endpoint_prefix = endpoint_prefix

	def __call__(self, *args, **kwargs):
		url = 'http://'+str(self.remote_ip)+':'+str(self.port)+'/'+self.endpoint_prefix+self.__name__
		# url = 'ws://'+str(self.remote_ip)+':'+str(self.port)+'/'+self.endpoint_prefix+self.__name__
		return self.tl.call_rpc(url, args, kwargs)

class SyncStub():

	def __init__(self, worker_ip='localhost', tl=None, port=comms_config.worker_port, rpc_name=None, endpoint_prefix=default_rpc_endpoint):
		self.remote_ip = worker_ip
		self.port = port
		self.tl = tl
		self.__name__ = rpc_name
		self.endpoint_prefix = endpoint_prefix

	def __call__(self, *args, **kwargs):
		url = 'http://'+str(self.remote_ip)+':'+str(self.port)+'/'+self.endpoint_prefix+self.__name__
		# url = 'ws://'+str(self.remote_ip)+':'+str(self.port)+'/'+self.endpoint_prefix+self.__name__
		return self.tl.call_rpc(url, args, kwargs).join()