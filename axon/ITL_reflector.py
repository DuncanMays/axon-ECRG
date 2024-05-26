import sys
sys.path.append('..')

import axon
import time
import threading
import websockets
from websockets.sync.server import serve as sync_serve

from concurrent.futures import Future

from .serializers import serialize, deserialize
from .transport_client import req_executor, error_handler, AsyncResultHandle
from .config import default_service_config
from .chunking import send_in_chunks, recv_chunks

TransportWorker = type(default_service_config['tl'])
http_tl = TransportWorker(8081)
reflector_node = None

class ITL_Client():

	def __init__(self, socket, name):
		self.socket = socket
		self.name = name

	def get_config(self):
		# the ITL client sends requests through an already established socket connection, so config info like the port number and scheme don't exist
		return None

	def call_rpc(self, url, args, kwargs):
		url_components = url.split('/')
		url_head = '/'.join(url_components[:3])		
		endpoint = '/' + '/'.join(url_components[3:])

		try:
			self.socket.send(endpoint)
			param_str = serialize((args, kwargs))
			send_in_chunks(self.socket, param_str)

			result_str = recv_chunks(self.socket)
			result_str = error_handler(result_str)
			return deserialize(result_str)

		except(websockets.ConnectionClosed) as e:
			self.on_close()
			raise e

	def on_close(self):
		global reflector_node
		reflector_node.remove_child(self.name)

def sock_serve_fn(websocket):
	global http_tl, reflector_node

	header_str = websocket.recv()
	name, profile_str = header_str.split('||', 1)
	profile = deserialize(profile_str)

	itl = ITL_Client(websocket, name)
	stub = axon.client.make_ServiceStub('ws://none:0000', itl, profile, stub_type=axon.stubs.SyncStub)
	reflector_node.add_child(name, stub)

	# blocks until the worker closes the connection
	while True:
		time.sleep(1_000_000)

def run(endpoint):
	global http_tl, reflector_node

	http_thread = threading.Thread(target=http_tl.run, daemon=True)
	http_thread.start()
	time.sleep(0.5)

	reflector_node = axon.worker.register_ServiceNode({}, endpoint, tl=http_tl)

	with sync_serve(sock_serve_fn, '0.0.0.0', 8008) as server:
		server.serve_forever()