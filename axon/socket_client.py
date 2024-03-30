from websockets.sync.client import connect

from .serializers import serialize, deserialize
from .transport_client import req_executor, error_handler, AsyncResultHandle
from .chunking import send_in_chunks, recv_chunks

class SocketTransportClient():

	def __init__(self):
		self.maxsize = 100_000

	def call_rpc_helper(self, url_head, endpoint, param_str):

		with connect(url_head) as socket:
			socket.send(endpoint)
			send_in_chunks(socket, param_str)
			result_str = recv_chunks(socket)
			return_obj = deserialize(result_str)

		return error_handler(return_obj)

	def call_rpc(self, url, args, kwargs):

		# split the endpoint from the url
		url_components = url.split('/')
		url_head = '/'.join(url_components[:3])
		endpoint = '/' + '/'.join(url_components[3:])

		param_str = serialize((args, kwargs))
		req_str = endpoint+' '+param_str

		future = req_executor.submit(self.call_rpc_helper, url_head, endpoint, param_str)
		return AsyncResultHandle(future)
