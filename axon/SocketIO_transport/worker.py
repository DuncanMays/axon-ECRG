import sys
sys.path.append('..')

import socketio
import cloudpickle
import traceback
import logging
import psutil

from concurrent.futures import ProcessPoolExecutor as PPE
from axon.transport_worker import AbstractTransportWorker
from axon.serializers import serialize, deserialize
from axon.SocketIO_transport import config
from aiohttp import web
from flask import Flask

class SocketIOTransportWorker(AbstractTransportWorker):

	def __init__(self, port=config.port):
		super().__init__()

		# all RPCs registered with this TL are stored here in this dict
		self.rpcs = {}
		self.port = port
		self.chunk_buffers = {}

		self.sio = socketio.Server(async_mode='threading')
		self.app = Flask(__name__)
		self.app.wsgi_app = socketio.WSGIApp(self.sio, self.app.wsgi_app)

		@self.sio.event
		def client_request(sid, req_str):
			endpoint, param_str = req_str.split('|', 1)
			result_str = self.invoke_RPC(endpoint, param_str, in_parallel=True)
			self.sio.emit('result_from_worker', to=sid, data=result_str)

		@self.sio.event
		def client_request_chunk(sid, req_str):
			chunk_num, num_chunks, endpoint, call_ID, chunk_str = req_str.split('|', 5)

			chunk_obj = {
				'chunk_str': chunk_str,
				'chunk_num': int(chunk_num)
			}

			if (call_ID in self.chunk_buffers):
				self.chunk_buffers[call_ID].append(chunk_obj)

			else :
				self.chunk_buffers[call_ID] = [chunk_obj]

			if (len(self.chunk_buffers[call_ID]) == int(num_chunks)):
				chunks = self.chunk_buffers[call_ID]
				chunks.sort(key=lambda x: x['chunk_num'])
				chunk_strs = [b['chunk_str'] for b in chunks]
				param_str = ''.join(chunk_strs)
				result_str = self.invoke_RPC(endpoint, param_str, in_parallel=True)
				self.sio.emit('result_from_worker', to=sid, data=result_str)

	def run(self):
		self.app.run(host='0.0.0.0', port=self.port)