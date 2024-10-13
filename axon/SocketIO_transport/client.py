from sys import path
path.append('..')

from axon.serializers import serialize, deserialize
from axon.transport_client import AbstractTransportClient, error_handler
from axon.SocketIO_transport import config
from concurrent.futures import Future
from math import ceil

import socketio
import random

def get_ID_generator(n=10_000):
	L = list(range(n))
	random.shuffle(L)
	while True:
		for l in L:
			yield str(l)

call_ID_gen = get_ID_generator()

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

		self.sio.connect(url_head)

		result_future = Future()
		
		def handle_result(result_str):
			result_future.set_result(result_str)
			self.sio.disconnect()

		self.sio.on('result_from_worker', handle_result)

		req_str = serialize((args, kwargs))
		chunk_size = 100_000

		if (len(req_str) < chunk_size):
			self.sio.emit('client_request', data=f'{endpoint}|{req_str}')

		else:
			num_chunks = ceil(len(req_str)/chunk_size)
			call_ID = next(call_ID_gen)

			for i in range(num_chunks):
				chunk_str = req_str[ chunk_size*i : chunk_size*(i+1) ]
				self.sio.emit('client_request_chunk', data=f'{str(i)}|{str(num_chunks)}|{endpoint}|{call_ID}|{chunk_str}')

		result_str = result_future.result()
		result_str = error_handler(result_str)
		return deserialize(result_str)