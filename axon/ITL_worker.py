import sys
sys.path.append('..')

from .transport_worker import invoke_RPC
from .serializers import serialize, deserialize
from .chunking import send_in_chunks, recv_chunks
from .stubs import add_url_defaults

from concurrent.futures import ProcessPoolExecutor as PPE
from types import SimpleNamespace

import socketio
import cloudpickle
import time
import sys
import traceback

class ITL_Worker():

	def __init__(self, url, name):
		self.name = name
		self.reflector_url = add_url_defaults(url, SimpleNamespace(port=5000, scheme='http'))
		self.rpcs = {}

	def run(self):

		# here we search through registered RPCs to find any top-level service nodes who's profile we send up to the reflector

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

		sio = socketio.Client()
		sio.connect(self.reflector_url)

		# this is the first message we'll send the reflector, containing the service name and its profile
		header_str = str(self.name)+'||'+profile_str
		sio.emit('worker_header', data=header_str)

		@sio.event
		def rpc_request(req_str):
			call_ID, endpoint, param_str = req_str.split('|', 3)

			return_object = {
				'errcode': 0,
				'result': None,
			}

			try:
				(fn, executor) = self.rpcs[endpoint]

				result_str = executor.submit(invoke_RPC, fn, param_str).result()
				result_str = f'0|{result_str}'

			except():
				result_str = serialize(traceback.format_exc(), sys.exc_info()[1])
				result_str = f'1|{result_str}'

			sio.emit('rpc_result', data=f'{call_ID}|{result_str}')

		while True:
			time.sleep(1_000_000)

	def register_RPC(self, fn, endpoint, executor):

		if isinstance(executor, PPE):
			fn = cloudpickle.dumps(fn)
		
		self.rpcs[endpoint] = (fn, executor)

	def deregister_RPC(self, endpoint):

		if endpoint in self.rpcs:
			del self.rpcs[endpoint]
		else:
			raise BaseException(f'No RPC registered at endpoint: {endpoint}')