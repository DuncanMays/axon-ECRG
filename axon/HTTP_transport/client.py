from sys import path
path.append('..')

from axon.serializers import serialize, deserialize
from axon.transport_client import AbstractTransportClient, http, error_handler
from axon.HTTP_transport import config

class HTTPTransportClient(AbstractTransportClient):

	def __init__(self):
		pass

	def get_config(self):
		return config

	def call_rpc(self, url, args, kwargs):

		resp = http.request('POST', url, fields={'msg': serialize((args, kwargs))})
		result_str = error_handler(resp.data.decode())
		return deserialize(result_str)