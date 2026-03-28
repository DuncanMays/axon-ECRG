import axon
import socketio

from functools import partial
from concurrent.futures import Future

from axon.serializers import serialize, deserialize
from axon.transport_client import AbstractTransportClient
from axon.utils import get_ID_generator
from axon.reflector.sio_chunking import sio_send, ChunkBuffer
from axon.reflector.config import passthrough_serialize, passthrough_deserialize

NAMESPACE = '/workers'


class CloudClient(AbstractTransportClient):

	def __init__(self, emit_fn, sid, name, logger):
		super().__init__()

		self._emit = emit_fn
		self._logger = logger
		self.sid = sid
		self.name = name
		self.pending_reqs = {}
		self.chunk_buffer = ChunkBuffer()
		self.call_ID_gen = get_ID_generator()

		self.serialize = passthrough_serialize
		self.deserialize = passthrough_deserialize

	def get_config(self):
		return None

	def net_call(self, url, param_str):

		url_components = url.split('/')
		endpoint = '/' + '/'.join(url_components[3:])

		call_ID = next(self.call_ID_gen)
		result_future = Future()
		self.pending_reqs[call_ID] = result_future

		self._logger.debug('RPC call to: %s for: %s call_ID: %s', self.sid, endpoint, call_ID)

		req_str = f'{call_ID}|{endpoint}|{param_str}'
		sio_send(partial(self._emit, to=self.sid), 'rpc_request', req_str)

		return result_future.result()

	def disconnect_handler(self):

		for call_ID in self.pending_reqs:
			result_str = serialize(BaseException('WorkerDisconnect'))
			result_str = f'1|{result_str}'
			self.pending_reqs[call_ID].set_result(result_str)


class CloudClientNamespace(socketio.Namespace):

	def __init__(self, http_node, logger):
		super().__init__(NAMESPACE)
		self._client_sid_map = {}
		self._http_node = http_node
		self._logger = logger

	def on_connect(self, sid, environ):
		self._logger.debug('New EdgeWorker connection: %s', sid)

	def on_disconnect(self, sid):
		if sid in self._client_sid_map:
			self._logger.debug('EdgeWorker %s disconnected', sid)
			client = self._client_sid_map.pop(sid)
			self._http_node.remove_child(client.name)
			client.disconnect_handler()

	def on_worker_header(self, sid, name):
		self._client_sid_map[sid] = CloudClient(self.emit, sid, name, self._logger)

	def on_update_profile(self, sid, profile_str):
		self._logger.debug('update_profile %s', sid)
		profile = deserialize(profile_str)
		client = self._client_sid_map[sid]
		stub = axon.client.make_ServiceStub('ws://none:0000', client, profile, stub_type=axon.stubs.SyncStub)
		self._http_node.add_child(client.name, stub)

	def on_rpc_result(self, sid, return_str):
		call_ID, result_str = return_str.split('|', 1)
		self._logger.debug('RPC response for call_ID: %s', call_ID)
		self._client_sid_map[sid].pending_reqs[call_ID].set_result(result_str)

	def on_rpc_result_chunk(self, sid, res_str):
		client = self._client_sid_map[sid]
		assembled = client.chunk_buffer.receive(res_str)
		if assembled is not None:
			call_ID, result_str = assembled.split('|', 1)
			self._logger.debug('received all chunks for call_ID: %s', call_ID)
			client.pending_reqs[call_ID].set_result(result_str)
