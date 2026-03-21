import sys
sys.path.append('..')

from axon.transport_worker import AbstractTransportWorker
from axon.serializers import serialize, deserialize
from axon.stubs import add_url_defaults
from axon.worker import TLSNs

from axon.reflector.sio_chunking import sio_send, ChunkBuffer

from concurrent.futures import Future, ProcessPoolExecutor as PPE
from types import SimpleNamespace

import socketio
import cloudpickle
import time
import sys
import traceback

class ITLW(AbstractTransportWorker):

	def __init__(self, name, url='http://143.198.32.69:5000'):
		super().__init__()

		self.name = name
		self.chunk_buffer = ChunkBuffer()
		self.reflector_url = add_url_defaults(url, SimpleNamespace(port=5000, scheme='http'))
		self.sio = socketio.Client()
		# for if an error means the worker must terminate
		self.terminal_error_future = Future()

		@self.sio.event
		def rpc_request(req_str):
			self.invoke_rpc_helper(req_str)

		@self.sio.event
		def rpc_request_chunk(event_str):
			assembled = self.chunk_buffer.receive(event_str)
			if assembled is not None:
				self.invoke_rpc_helper(assembled)

	def invoke_rpc_helper(self, req_str):
		call_ID, endpoint, param_str = req_str.split('|', 2)

		result_str = self.invoke_RPC(endpoint, param_str, in_parallel=True)

		try:
			sio_send(self.sio, 'rpc_result', f'{call_ID}|{result_str}')

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