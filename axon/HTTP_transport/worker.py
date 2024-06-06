import sys
sys.path.append('..')

from flask import Flask
from flask import request as route_req
from concurrent.futures import ProcessPoolExecutor as PPE

import traceback
import logging
import cloudpickle

from axon.transport_worker import AbstractTransportWorker, invoke_RPC
from axon.serializers import serialize, deserialize
from axon.HTTP_transport import config

class HTTPTransportWorker(AbstractTransportWorker):

	def __init__(self, port=config.port):
		# all RPCs registered with this TL are stored here in this dict
		self.rpcs = {}

		# removes the startup text
		cli = sys.modules['flask.cli']
		cli.show_server_banner = lambda *x: None
		log = logging.getLogger('werkzeug')
		log.disabled = True

		# the app that listens for incomming http requests
		self.app = Flask('HTTPTransportWorker')	
		self.port = port

		# the route that listens for incomming RPC requests
		@self.app.route('/', defaults={'path': ''}, methods=['POST'])
		@self.app.route('/<path:path>', methods=['POST'])
		def catch_all(path):
			
			try:
				path = '/'+path
				(fn, executor) = self.rpcs[path]

				param_str = route_req.form['msg']
				result_str = executor.submit(invoke_RPC, fn, param_str, in_parallel=True).result()
				result_str = f'0|{result_str}'

			except:
				result_str = serialize((traceback.format_exc(), sys.exc_info()[1]))
				result_str = f'1|{result_str}'

			return result_str

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