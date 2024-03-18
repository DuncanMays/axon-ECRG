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
import sys
import traceback

class ITL_Worker():

	def __init__(self, reflector_url):
		self.reflector_url = reflector_url
		self.rpcs = {}

	def run(self):
		
		(fn, _) = self.rpcs['/test_service']
		profile = fn()
		profile = serialize(profile)

		with connect(self.reflector_url) as connection:
			connection.send(profile)

			while True:

				req_str = None
				try:
					# blocks until a message is recieved
					req_str = connection.recv()

				except(websockets.exceptions.ConnectionClosedOK):
					self.close()
					break

				return_object = {
					'errcode': 0,
					'result': None,
				}

				try:
					endpoint, param_str = req_str.split(' ', 1)
					endpoint = endpoint.replace('//', '/')

					(fn, executor) = self.rpcs[endpoint]

					future = executor.submit(invoke_RPC, fn, param_str)
					return_object['result'] = future.result()

				except():
					return_object['errcode'] = 1
					return_object['result'] = (traceback.format_exc(), sys.exc_info()[1])


				connection.send(serialize(return_object))

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

