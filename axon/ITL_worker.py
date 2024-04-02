import sys
sys.path.append('..')
from .config import comms_config
from .transport_worker import invoke_RPC
from .serializers import serialize, deserialize
from .chunking import send_in_chunks, recv_chunks

from concurrent.futures import ProcessPoolExecutor as PPE
import websockets
from websockets.sync.client import connect
import cloudpickle
import time
import sys
import traceback

class ITL_Worker():

	def __init__(self, reflector_url, name):
		self.name = name
		self.reflector_url = reflector_url
		self.rpcs = {}

	def run(self):

		# here we search through registered RPCs to find any top-level service node's who's profile we send up to the reflector

		endpoints = self.rpcs.keys()
		# filter out the keys that end in __call__, since they're endpoints for RPCs, not get_profile
		profile_endpoints = filter(lambda x : not x[::-1].split('/', 1)[0] == '__llac__', endpoints)

		profile = {}

		for pe in profile_endpoints:
			parent = pe.split('/', 2)[1]

			if parent in profile:
				if (len(pe) < len(profile[parent])):
					profile[parent] = pe

			else:
				profile[parent] = pe
		
		for service_name in profile:
			endpoint = profile[service_name]
			(fn, _) = self.rpcs[endpoint]
			profile[service_name] = fn()

		profile_str = serialize(profile)

		print(len(profile_str))

		# this is the first message we'll send the reflector, containing the service name and its profile
		header_str = str(self.name)+'||'+profile_str

		with connect(self.reflector_url) as connection:
			connection.send(header_str)

			while True:

				endpoint = connection.recv()
				endpoint = endpoint.replace('//', '/')
				param_str = recv_chunks(connection)

				return_object = {
					'errcode': 0,
					'result': None,
				}

				try:
					(fn, executor) = self.rpcs[endpoint]

					future = executor.submit(invoke_RPC, fn, param_str)
					return_object['result'] = future.result()

				except():
					return_object['errcode'] = 1
					return_object['result'] = (traceback.format_exc(), sys.exc_info()[1])

				send_in_chunks(connection, serialize(return_object))

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

