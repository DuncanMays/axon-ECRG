import sys
sys.path.append('..')

import axon
import time
import threading
import websockets
import logging
import psutil

from websockets.sync.server import serve as sync_serve
from concurrent.futures import Future
from threading import Timer

from .serializers import serialize, deserialize
from .transport_client import req_executor, error_handler, AsyncResultHandle
from .config import transport, default_service_config
from .chunking import send_in_chunks, recv_chunks
from .HTTP_transport.config import port as default_http_port

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

c_handler = logging.StreamHandler()
f_handler = logging.FileHandler('reflector.log')

log_format = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
c_handler.setFormatter(log_format)
f_handler.setFormatter(log_format)

logger.addHandler(c_handler)
logger.addHandler(f_handler)

reflector_node = None
http_tl = None

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

		logger.debug('RPC call to %s for %s', self.socket.remote_address, endpoint)

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
	global logger, reflector_node

	try:
		logger.debug('New connection from worker at %s', websocket.remote_address)

		header_str = websocket.recv()
		name, profile_str = header_str.split('||', 1)
		profile = deserialize(profile_str)

		itl = ITL_Client(websocket, name)
		stub = axon.client.make_ServiceStub('ws://none:0000', itl, profile, stub_type=axon.stubs.SyncStub)
		reflector_node.add_child(name, stub)

		# blocks to keep the socket open until the worker closes the connection
		while True:
			time.sleep(1_000_000)

	except(BaseException) as e:
		logger.exception("An exception occurred while handling a socket connection to worker")
		websocket.close()

sample = psutil.net_io_counters()
last_bytes_sent = sample.bytes_sent
last_bytes_recv = sample.bytes_recv
# log usage metrics every hour
log_interval = 60*60
def log_usage():
	global last_bytes_sent, last_bytes_recv

	cpu = psutil.cpu_percent()
	ram = psutil.virtual_memory().percent
	net = psutil.net_io_counters()
	sent = net.bytes_sent - last_bytes_sent
	last_bytes_sent = net.bytes_sent
	recv = net.bytes_recv - last_bytes_recv
	last_bytes_recv = net.bytes_recv

	logger.info('usage: CPU %s RAM %s bytes_sent %s bytes_recv %s', cpu, ram, sent, recv)

def run(endpoint='reflected_services', ws_port=8008, http_port=default_http_port):
	global reflector_node, http_tl

	http_tl = transport.worker(http_port)

	http_thread = threading.Thread(target=http_tl.run, daemon=True)
	http_thread.start()
	time.sleep(0.5)

	# reflector_node = axon.worker.register_ServiceNode({}, endpoint, tl=http_tl)
	reflector_node = axon.worker.ServiceNode({}, endpoint, tl=http_tl)

	logger.debug('Reflector start')

	with sync_serve(sock_serve_fn, '0.0.0.0', ws_port) as server:
		server.serve_forever()