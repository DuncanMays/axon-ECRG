from axon.transport_worker import AbstractTransportWorker
from axon.serializers import serialize
from axon.chunking import send_in_chunks, recv_chunks
from axon.socket_transport import config

from concurrent.futures import ProcessPoolExecutor as PPE

import websockets.sync.server as sync_server
import sys
import traceback

class SocketTransportWorker(AbstractTransportWorker):

	def __init__(self, port=config.port):
		super().__init__()
		
		self.port = port
		self.rpcs = {}
		self.maxsize = 100_000

	def run(self):
		with sync_server.serve(self.sock_serve_fn, '127.0.0.1', self.port) as server:
			server.serve_forever()

	def sock_serve_fn(self, websocket):

		path = websocket.recv()
		path = path.replace('//', '/')

		param_str = recv_chunks(websocket)

		result_str = self.invoke_RPC(path, param_str, in_parallel=True)

		send_in_chunks(websocket, result_str)