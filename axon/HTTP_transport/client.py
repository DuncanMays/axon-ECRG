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

	def net_call(self, url, param_str):
		resp = http.request('POST', url, fields={'msg': param_str})
		return resp.data.decode()