from .config import comms_config, default_rpc_config
from .transport_client import call_rpc

class GenericStub():

	def __init__(self, worker_ip='localhost', port=comms_config.worker_port, rpc_name=None, endpoint_prefix=default_rpc_config['endpoint_prefix']):
		self.remote_ip = worker_ip
		self.port = port
		self.__name__ = rpc_name
		self.endpoint_prefix = endpoint_prefix

	def __call__(self, *args, **kwargs):
		url = 'http://'+str(self.remote_ip)+':'+str(self.port)+'/'+self.endpoint_prefix+self.__name__
		return call_rpc(url, args, kwargs)

class SyncStub():

	def __init__(self, worker_ip='localhost', port=comms_config.worker_port, rpc_name=None, endpoint_prefix=default_rpc_config['endpoint_prefix']):
		self.remote_ip = worker_ip
		self.port = port
		self.__name__ = rpc_name
		self.endpoint_prefix = endpoint_prefix

	def __call__(self, *args, **kwargs):
		url = 'http://'+str(self.remote_ip)+':'+str(self.port)+'/'+self.endpoint_prefix+self.__name__
		return call_rpc(url, args, kwargs).join()