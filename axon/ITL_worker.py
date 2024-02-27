from .config import comms_config
from .transport_worker import invoke_RPC

from concurrent.futures import ProcessPoolExecutor as PPE
from websockets.sync.client import connect
import cloudpickle

class ITL_Worker():

	def __init__(self, reflector_ur):
		self.reflector_url = reflector_url
		self.rpcs = {}

		# create connection to reflector
		self.connection = connect(reflector_url)

	def run(self):
		
		(fn, _) = self.rpcs['/_get_profile']
		profile = fn()
		self.connection.send(profile)

		# start listening for incomming requests
		req_str = self.connection.recv()
		endpoint, param_str = req_str.split(' ', 1)
		endpoint = endpoint.replace('//', '/')

		(fn, executor) = self.rpcs[endpoint]

		future = executor.submit(invoke_RPC, fn, param_str)

		self.connection.send(future.result())


	def register_RPC(self, fn, endpoint, executor):

		if isinstance(executor, PPE):
			fn = cloudpickle.dumps(fn)
		
		self.rpcs[endpoint] = (fn, executor)

	def deregister_RPC(self, endpoint):

		if endpoint in self.rpcs:
			del self.rpcs[endpoint]
		else:
			raise BaseException(f'No RPC registered at endpoint: {endpoint}')