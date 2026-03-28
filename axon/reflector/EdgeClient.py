import sys
sys.path.append('..')

import axon

from functools import partial
from concurrent.futures import Future

from axon.transport_client import AbstractTransportClient
from axon.utils import get_ID_generator
from axon.serializers import serialize
from axon.reflector.sio_chunking import sio_send, ChunkBuffer
from axon.reflector.CloudWorker import NAMESPACE

class EdgeClient(AbstractTransportClient):

	def __init__(self, sio):
		super().__init__()

		self.sio = sio
		self.pending_reqs = {}
		self.chunk_buffer = ChunkBuffer()
		self.call_ID_gen = get_ID_generator()
		self.init_future = Future()

		self.sio.emit('client_header', namespace=NAMESPACE, callback=lambda: self.init_future.set_result(None))

		@self.sio.on('rpc_result', namespace=NAMESPACE)
		def rpc_result(return_str):
			call_ID, result_str = return_str.split('|', 1)
			result_future = self.pending_reqs[call_ID]
			result_future.set_result(result_str)

		@self.sio.on('rpc_result_chunk', namespace=NAMESPACE)
		def rpc_result_chunk(event_str):
			assembled = self.chunk_buffer.receive(event_str)
			if assembled is not None:
				call_ID, result_str = assembled.split('|', 1)
				self.pending_reqs[call_ID].set_result(result_str)

		@self.sio.on('disconnect', namespace=NAMESPACE)
		def disconnect(e):
			self.disconnect_handler()

	def get_config(self):
		return None

	def net_call(self, url, param_str):

		self.init_future.result()

		url_components = url.split('/')
		endpoint = '/' + '/'.join(url_components[3:])

		call_ID = next(self.call_ID_gen)
		result_future = Future()
		self.pending_reqs[call_ID] = result_future

		req_str = f'{call_ID}|{endpoint}|{param_str}'
		sio_send(partial(self.sio.emit, namespace=NAMESPACE), 'rpc_request', req_str)

		return result_future.result()

	def disconnect_handler(self):

		for call_ID in self.pending_reqs:
			result_str = serialize(BaseException('WorkerDisconnect'))
			result_str = f'1|{result_str}'
			self.pending_reqs[call_ID].set_result(result_str)
