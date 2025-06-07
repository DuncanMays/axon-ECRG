import sys
sys.path.append('..')

from axon.transport_worker import invoke_RPC, AbstractTransportWorker
from axon.serializers import serialize, deserialize
from axon.chunking import send_in_chunks, recv_chunks
from axon.stubs import add_url_defaults
from axon.worker import TLSNs

from concurrent.futures import Future, ProcessPoolExecutor as PPE
from types import SimpleNamespace
from math import ceil

import socketio
import cloudpickle
import time
import sys
import traceback

class ITLW(AbstractTransportWorker):

	def __init__(self, name, url='http://143.198.32.69:5000'):
		super().__init__()

		self.name = name
		self.reflector_url = add_url_defaults(url, SimpleNamespace(port=5000, scheme='http'))
		self.rpcs = {}
		self.sio = None

	def run(self):

		self.sio = socketio.Client()
		self.sio.connect(self.reflector_url)

		# this is the first message we'll send the reflector, containing the worker name
		self.sio.emit('worker_header', data=str(self.name))

		self.update_profile()

		error_future = Future()

		@self.sio.event
		def rpc_request(req_str):
			try:

				try:
					call_ID, endpoint, param_str = req_str.split('|', 3)
					(fn, executor) = self.rpcs[endpoint]

					result_str = executor.submit(invoke_RPC, fn, param_str, in_parallel=True, serialize=self.serialize, deserialize=self.deserialize).result()
					result_str = f'0|{result_str}'

				except:
					result_str = serialize((traceback.format_exc(), sys.exc_info()[1]))
					result_str = f'1|{result_str}'

				chunk_size = 100_000

				if (len(result_str) < chunk_size):
					self.sio.emit('rpc_result', data=f'{call_ID}|{result_str}')

				else:
					num_chunks = ceil(len(result_str)/chunk_size)

					for i in range(num_chunks):
						chunk_str = result_str[ chunk_size*i : chunk_size*(i+1) ]
						self.sio.emit('rpc_result_chunk', data=f'{str(i)}|{str(num_chunks)}|{call_ID}|{chunk_str}')
			except:
				error = sys.exc_info()[1]
				error_future.set_result(error)

		raise(error_future.result())

	def update_profile(self):
		
		tlsn = TLSNs[id(self)]
		profile = tlsn.get_profile()
		self.sio.emit('update_profile', data=serialize(profile))