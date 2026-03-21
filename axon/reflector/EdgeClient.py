import sys
sys.path.append('..')

import axon

from concurrent.futures import Future

from axon.transport_client import req_executor, error_handler, AsyncResultHandle, AbstractTransportClient
from axon.utils import get_ID_generator
from axon.serializers import serialize

from axon.reflector.sio_chunking import sio_send, ChunkBuffer

class EdgeClient(AbstractTransportClient):

	def __init__(self, sio):
		super().__init__()
		
		self.sio = sio
		self.pending_reqs = {}
		self.chunk_buffer = ChunkBuffer()
		self.call_ID_gen = get_ID_generator()
		self.init_future = Future()

		self.sio.emit('client_header', callback=lambda: self.init_future.set_result(None))

		@self.sio.event
		def rpc_result(return_str):
			call_ID, result_str = return_str.split('|', 1)
			# logger.debug('RPC response for call_ID: %s', call_ID)
			result_future = self.pending_reqs[call_ID]
			result_future.set_result(result_str)

		@self.sio.event
		def rpc_result_chunk(event_str):
			assembled = self.chunk_buffer.receive(event_str)
			if assembled is not None:
				call_ID, result_str = assembled.split('|', 1)
				self.pending_reqs[call_ID].set_result(result_str)

		@self.sio.event
		def disconnect(e):
			self.disconnect_handler()

	def get_config(self):
		# the ITL client sends requests through an already established socket connection, so config info like the port number and scheme don't exist
		return None

	def net_call(self, url, param_str):

		self.init_future.result()

		url_components = url.split('/')
		url_head = '/'.join(url_components[:3])
		endpoint = '/' + '/'.join(url_components[3:])

		call_ID = next(self.call_ID_gen)
		result_future = Future()
		self.pending_reqs[call_ID] = result_future

		# logger.debug('RPC call to: %s for: %s call_ID: %s', endpoint, call_ID)

		req_str = f'{call_ID}|{endpoint}|{param_str}'
		sio_send(self.sio.emit, 'rpc_request', req_str)

		return result_future.result()

	def disconnect_handler(self):

		# send a worker disconnect error back through each pending request
		for call_ID in self.pending_reqs:
			result_str = serialize(BaseException('WorkerDisconnect'))
			result_str = f'1|{result_str}'
			self.pending_reqs[call_ID].set_result(result_str)