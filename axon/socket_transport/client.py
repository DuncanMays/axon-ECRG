from sys import path
path.append('..')

from axon.serializers import serialize, deserialize
from axon.transport_client import AbstractTransportClient, req_executor, error_handler, AsyncResultHandle
from axon.chunking import send_in_chunks, recv_chunks
from axon.socket_transport import config

from websockets.sync.client import connect

class SocketTransportClient(AbstractTransportClient):

	def __init__(self, port=config.port):
		self.maxsize = 100_000

	def get_config(self):
		return config

	def call_rpc_helper(self, url_head, endpoint, param_str):
		result = None

		with connect(url_head) as socket:
			socket.send(endpoint)
			send_in_chunks(socket, param_str)
			result_str = recv_chunks(socket)
			result_str = error_handler(result_str)
			result = deserialize(result_str)

		return result

	def call_rpc(self, url, args, kwargs):

		# split the endpoint from the url
		url_components = url.split('/')
		url_head = '/'.join(url_components[:3])		
		endpoint = '/' + '/'.join(url_components[3:])

		param_str = serialize((args, kwargs))
		req_str = endpoint+' '+param_str

		future = req_executor.submit(self.call_rpc_helper, url_head, endpoint, param_str)
		return AsyncResultHandle(future)