import sys
sys.path.append('..')

import socketio
import cloudpickle
import traceback
import logging
import psutil

from concurrent.futures import ProcessPoolExecutor as PPE
from axon.transport_worker import AbstractTransportWorker, invoke_RPC
from axon.serializers import serialize, deserialize
from axon.SocketIO_transport import config
from aiohttp import web
from flask import Flask

class SocketIOTransportWorker(AbstractTransportWorker):

	def __init__(self, port=config.port):
		# all RPCs registered with this TL are stored here in this dict
		self.rpcs = {}
		self.port = port

		self.sio = socketio.Server(async_mode='threading')
		self.app = Flask(__name__)
		self.app.wsgi_app = socketio.WSGIApp(self.sio, self.app.wsgi_app)

		@self.sio.event
		def client_request(sid, req_str):
			result_str = None
			endpoint, param_str = req_str.split('|', 1)

			try:
				(fn, executor) = self.rpcs[endpoint]

				result_str = executor.submit(invoke_RPC, fn, param_str, in_parallel=True).result()
				result_str = f'0|{result_str}'

			except:
				result_str = serialize((traceback.format_exc(), sys.exc_info()[1]))
				result_str = f'1|{result_str}'

			self.sio.emit('result_from_worker', to=sid, data=result_str)

	def run(self):
		self.app.run(host='0.0.0.0', port=self.port)

	def register_RPC(self, fn, endpoint, executor):

		if isinstance(executor, PPE):
			fn = cloudpickle.dumps(fn)

		self.rpcs[endpoint] = (fn, executor)

	def deregister_RPC(self, endpoint):

		if endpoint in self.rpcs:
			del self.rpcs[endpoint]
		else:
			raise BaseException(f'No RPC registered at endpoint: {endpoint}')