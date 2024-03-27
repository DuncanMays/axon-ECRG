import sys
sys.path.append('..')

import axon
import time
import threading
import websockets.sync.server as sync_server

from concurrent.futures import Future

from .serializers import serialize, deserialize
from .transport_client import req_executor, error_handler, AsyncResultHandle
from .config import default_service_config

TransportWorker = type(default_service_config['tl'])
http_tl = TransportWorker(8081)
reflector_node = None

class ITL_Client():

	def __init__(self, socket):
		self.socket = socket

	def call_rpc_helper(self, endpoint, args, kwargs):
		param_str = serialize((args, kwargs))
		req_str = endpoint+' '+param_str
		self.socket.send(req_str)
		result_str = self.socket.recv()
		wrapped_result = deserialize(result_str)
		return error_handler(wrapped_result)

	def call_rpc(self, endpoint, args, kwargs):
		future = req_executor.submit(self.call_rpc_helper, endpoint, args, kwargs)
		return AsyncResultHandle(future)

def sock_serve_fn(websocket):
	global http_tl, reflector_node

	header_str = websocket.recv()
	name, profile_str = header_str.split('||', 1)
	profile = deserialize(profile_str)

	itl = ITL_Client(websocket)
	stub = axon.client.make_ServiceStub('', itl, profile, stub_type=axon.stubs.SyncStub)
	reflector_node.add_child(name, stub) 

	# blocks until the worker closes the connection
	time.sleep(1_000_000)

def run(endpoint):
	global http_tl, reflector_node

	http_thread = threading.Thread(target=http_tl.run, daemon=True)
	http_thread.start()
	time.sleep(0.5)

	reflector_node = axon.worker.register_ServiceNode({}, endpoint, tl=http_tl)

	with sync_server.serve(sock_serve_fn, '127.0.0.1', 8080) as server:
		server.serve_forever()