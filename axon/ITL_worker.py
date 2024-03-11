import sys
sys.path.append('..')

from .config import comms_config
from .transport_worker import invoke_RPC
from .serializers import serialize, deserialize

from concurrent.futures import ProcessPoolExecutor as PPE
import websockets
from websockets.sync.client import connect
import cloudpickle
import time

class ITL_Worker():

	def __init__(self, reflector_url):
		self.reflector_url = reflector_url
		self.rpcs = {}

		# create connection to reflector
		self.connection = connect(reflector_url)

	def run(self):
		
		(fn, _) = self.rpcs['/test_service']
		profile = fn()
		profile = serialize(profile)
		self.connection.send(profile)

		while True:

			req_str = None
			try:
				# blocks until a message is recieved
				req_str = self.connection.recv()

			except(websockets.exceptions.ConnectionClosedOK):
				self.close()
				break

			endpoint, param_str = req_str.split(' ', 1)
			endpoint = endpoint.replace('//', '/')

			(fn, executor) = self.rpcs[endpoint]

			future = executor.submit(invoke_RPC, fn, param_str)

			self.connection.send(future.result())

	def close(self):
		self.connection.close()

	def register_RPC(self, fn, endpoint, executor):

		if isinstance(executor, PPE):
			fn = cloudpickle.dumps(fn)
		
		self.rpcs[endpoint] = (fn, executor)

	def deregister_RPC(self, endpoint):

		if endpoint in self.rpcs:
			del self.rpcs[endpoint]
		else:
			raise BaseException(f'No RPC registered at endpoint: {endpoint}')

if (__name__ == '__main__'):
	itlw = ITL_Worker('ws://localhost:8080')

