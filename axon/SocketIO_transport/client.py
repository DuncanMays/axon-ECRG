from sys import path
path.append('..')

from axon.serializers import serialize, deserialize
from axon.transport_client import AbstractTransportClient, error_handler
from axon.SocketIO_transport import config
from concurrent.futures import Future

import socketio

class SocketIOTransportClient(AbstractTransportClient):

	def __init__(self):
		self.sio = socketio.Client()

	def get_config(self):
		return config

	def call_rpc(self, url, args, kwargs):

		# split the endpoint from the url
		url_components = url.split('/')
		url_head = '/'.join(url_components[:3])		
		endpoint = '/' + '/'.join(url_components[3:])

		result_future = Future()
		def handle_result(result_str):
			result_future.set_result(result_str)
			self.sio.disconnect()

		self.sio.connect(url_head)
		self.sio.on('result_from_worker', handle_result)
		self.sio.emit('client_request', data=f'{endpoint}|{serialize((args, kwargs))}')

		result_str = result_future.result()
		result_str = error_handler(result_str)
		return deserialize(result_str)