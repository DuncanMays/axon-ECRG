# from .config import comms_config
from .transport_worker import invoke_RPC
from .serializers import serialize
from .chunking import send_in_chunks, recv_chunks

from concurrent.futures import ProcessPoolExecutor as PPE
import websockets.sync.server as sync_server
import cloudpickle
import sys
import traceback

class SocketTransportWorker():

	def __init__(self, port=8001):
		self.port = port
		self.rpcs = {}
		self.maxsize = 100_000

	def run(self):
		with sync_server.serve(self.sock_serve_fn, '127.0.0.1', self.port) as server:
			server.serve_forever()

	def sock_serve_fn(self, websocket):

		return_object = {
			'errcode': 0,
			'result': None,
		}
		
		try:
			endpoint = websocket.recv()
			endpoint = endpoint.replace('//', '/')

			param_str = recv_chunks(websocket)

			(fn, executor) = self.rpcs[endpoint]
			future = executor.submit(invoke_RPC, fn, param_str)
			return_object['result'] = future.result()
			
		except:
			return_object['errcode'] = 1
			return_object['result'] = (traceback.format_exc(), sys.exc_info()[1])
			
		result_str = serialize(return_object)

		send_in_chunks(websocket, result_str)

	def register_RPC(self, fn, endpoint, executor):

		if isinstance(executor, PPE):
			fn = cloudpickle.dumps(fn)
		
		self.rpcs[endpoint] = (fn, executor)

	def deregister_RPC(self, endpoint):

		if endpoint in self.rpcs:
			del self.rpcs[endpoint]
		else:
			raise BaseException(f'No RPC registered at endpoint: {endpoint}')