import sys
sys.path.append('..')

from axon.transport_worker import AbstractTransportWorker
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
		self.chunk_buffers = {}
		self.reflector_url = add_url_defaults(url, SimpleNamespace(port=5000, scheme='http'))
		self.sio = socketio.Client()
		# for if an error means the worker must terminate
		self.terminal_error_future = Future()

		@self.sio.event
		def rpc_request(req_str):
			self.invoke_rpc_helper(req_str)

		@self.sio.event
		def rpc_request_chunk(event_str):

			chunk_num, num_chunks, call_ID, chunk_str = event_str.split('|', 3)

			chunk_obj = {
				'chunk_str': chunk_str,
				'chunk_num': int(chunk_num)
			}

			if (call_ID in self.chunk_buffers):
				self.chunk_buffers[call_ID].append(chunk_obj)

			else :
				self.chunk_buffers[call_ID] = [chunk_obj]

			if (len(self.chunk_buffers[call_ID]) == int(num_chunks)):

				chunks = self.chunk_buffers[call_ID]
				chunks.sort(key=lambda x: x['chunk_num'])
				chunk_strs = [b['chunk_str'] for b in chunks]
				req_str = ''.join(chunk_strs)

				self.invoke_rpc_helper(req_str)

	def invoke_rpc_helper(self, req_str):
		call_ID, endpoint, param_str = req_str.split('|', 3)

		result_str = self.invoke_RPC(endpoint, param_str, in_parallel=True)

		chunk_size = 100_000

		try:
			if (len(result_str) < chunk_size):
				self.sio.emit('rpc_result', data=f'{call_ID}|{result_str}')

			else:
				num_chunks = ceil(len(result_str)/chunk_size)

				for i in range(num_chunks):
					chunk_str = result_str[ chunk_size*i : chunk_size*(i+1) ]
					self.sio.emit('rpc_result_chunk', data=f'{str(i)}|{str(num_chunks)}|{call_ID}|{chunk_str}')

		except(BaseException):
			error = sys.exc_info()[1]
			self.terminal_error_future.set_result(error)

	def run(self):

		self.sio.connect(self.reflector_url)

		# this is the first message we'll send the reflector, containing the worker name
		self.sio.emit('worker_header', data=str(self.name))

		self.update_profile()

		raise(self.terminal_error_future.result())

	def update_profile(self):
		
		tlsn = TLSNs[id(self)]
		profile = tlsn.get_profile()
		self.sio.emit('update_profile', data=serialize(profile))