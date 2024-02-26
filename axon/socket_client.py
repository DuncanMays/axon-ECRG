from websockets.sync.client import connect

from .serializers import serialize, deserialize
from .transport_client import req_executor, error_handler, AsyncResultHandle

class SocketTransportClient():

	def __init__(self):
		pass

	def call_rpc_helper(self, url_head, req_str):
		with connect(url_head) as socket:
			socket.send(req_str)
			return_obj = deserialize(socket.recv())

		return error_handler(return_obj)

	def call_rpc(self, url, args, kwargs):

		# split the endpoint from the url
		url_components = url.split('/')
		url_head = '/'.join(url_components[:3])
		endpoint = '/' + '/'.join(url_components[3:])

		param_str = serialize((args, kwargs))
		req_str = endpoint+' '+param_str

		future = req_executor.submit(self.call_rpc_helper, url_head, req_str)
		return AsyncResultHandle(future)
