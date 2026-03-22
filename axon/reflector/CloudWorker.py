import sys
import socketio

from functools import partial
from concurrent.futures import Future
from copy import copy

from axon.transport_worker import AbstractTransportWorker
from axon.reflector.sio_chunking import sio_send, ChunkBuffer
from axon.reflector.config import passthrough_serialize, passthrough_deserialize

NAMESPACE = '/clients'


class CloudWorker(AbstractTransportWorker):

	def __init__(self, emit_fn):
		super().__init__()

		self._emit = emit_fn
		self.chunk_buffer = ChunkBuffer()
		self.terminal_error_future = Future()

		self.serialize = passthrough_serialize
		self.deserialize = passthrough_deserialize

	def invoke_rpc_helper(self, req_str):
		call_ID, endpoint, param_str = req_str.split('|', 2)

		result_str = self.invoke_RPC(endpoint, param_str, in_parallel=True)

		try:
			sio_send(self._emit, 'rpc_result', f'{call_ID}|{result_str}')

		except BaseException:
			error = sys.exc_info()[1]
			self.terminal_error_future.set_result(error)

	def run(self):
		raise self.terminal_error_future.result()


class CloudWorkerNamespace(socketio.Namespace):

	def __init__(self, http_node, logger):
		super().__init__(NAMESPACE)
		self._worker_sid_map = {}
		self._http_node = http_node
		self._logger = logger

	def on_connect(self, sid, environ):
		self._logger.debug('New EdgeClient connection: %s', sid)

	def on_disconnect(self, sid):
		if sid in self._worker_sid_map:
			del self._worker_sid_map[sid]

	def on_client_header(self, sid):
		worker = CloudWorker(partial(self.emit, to=sid))
		worker.rpcs = copy(self._http_node.tl.rpcs)
		self._worker_sid_map[sid] = worker

	def on_rpc_request(self, sid, req_str):
		self._worker_sid_map[sid].invoke_rpc_helper(req_str)

	def on_rpc_request_chunk(self, sid, event_str):
		worker = self._worker_sid_map[sid]
		assembled = worker.chunk_buffer.receive(event_str)
		if assembled is not None:
			worker.invoke_rpc_helper(assembled)
