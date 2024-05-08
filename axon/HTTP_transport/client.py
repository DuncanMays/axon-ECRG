from sys import path
path.append('..')

from axon.serializers import serialize, deserialize
from axon.transport_client import AbstractTransportClient, http, req_executor, error_handler, AsyncResultHandle
from axon.HTTP_transport import config

class HTTPTransportClient(AbstractTransportClient):

	def __init__(self):
		pass

	def get_config(self):
		return config

	def call_rpc_helper(self, url, data):

		resp = http.request('POST', url, fields=data)
		result_str = error_handler(resp.data.decode())
		return deserialize(result_str)

	def call_rpc(self, url, args, kwargs):
		future = req_executor.submit(self.call_rpc_helper, url, {'msg': serialize((args, kwargs))})
		return AsyncResultHandle(future)