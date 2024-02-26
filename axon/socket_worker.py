from .config import comms_config
from .transport_worker import invoke_RPC

from concurrent.futures import ProcessPoolExecutor as PPE
import websockets.sync.server as sync_server
import cloudpickle

class SocketTransportWorker():

	def __init__(self, port=comms_config.worker_port+1):
		self.port = port
		self.rpcs = {}

	def run(self):
		with sync_server.serve(self.sock_serve_fn, '127.0.0.1', self.port) as server:
			server.serve_forever()

	def sock_serve_fn(self, websocket):
		req_str = websocket.recv()
		endpoint, param_str = req_str.split(' ', 1)
		endpoint = endpoint.replace('//', '/')

		(fn, executor) = self.rpcs[endpoint]

		future = executor.submit(invoke_RPC, fn, param_str)

		websocket.send(future.result())

	def register_RPC(self, fn, endpoint, executor):

		if isinstance(executor, PPE):
			fn = cloudpickle.dumps(fn)
		
		self.rpcs[endpoint] = (fn, executor)

	def deregister_RPC(self, endpoint):

		if endpoint in self.rpcs:
			del self.rpcs[endpoint]
		else:
			raise BaseException(f'No RPC registered at endpoint: {endpoint}')