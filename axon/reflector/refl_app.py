import sys
sys.path.append('..')

import axon
import time
import threading
import socketio
import logging

from concurrent.futures import Future, ThreadPoolExecutor
from functools import partial
from flask import Flask
from copy import copy

from axon.serializers import serialize, deserialize
from axon.transport_client import AbstractTransportClient
from axon.transport_worker import AbstractTransportWorker
from axon.config import transport
from axon.HTTP_transport.config import port as default_http_port
from axon.utils import get_ID_generator

from axon.reflector import config as refl_config
from axon.reflector.sio_chunking import sio_send, ChunkBuffer

sio = socketio.Server(async_mode='threading')

http_node = None
socket_node = None

client_sid_map = {}
worker_sid_map = {}

def null_serialize(params):
	
	if (params == ((), {})):
		return serialize(((), {}))

	if ("__profile_flag__" in params):
		return serialize(params)

	return params[0][0]

def null_deserialize(input_str):

	if (input_str == serialize(((), {}))):
		return ((), {})

	return (input_str, ), {}

logger = None
def init_logger():
	global logger

	logger = logging.getLogger(__name__)
	logger.setLevel(logging.DEBUG)

	c_handler = logging.StreamHandler()
	f_handler = logging.FileHandler(refl_config.log_file)

	log_format = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
	c_handler.setFormatter(log_format)
	f_handler.setFormatter(log_format)

	logger.addHandler(c_handler)
	logger.addHandler(f_handler)

# created on the cloud/reflector side when an EdgeWorker connects
class CloudClient(AbstractTransportClient):

	def __init__(self, sio, sid, name):
		super().__init__()
		
		self.sio = sio
		self.sid = sid
		self.name = name
		self.pending_reqs = {}
		self.chunk_buffer = ChunkBuffer()
		self.call_ID_gen = get_ID_generator()

		self.serialize = null_serialize
		self.deserialize = null_deserialize

	def get_config(self):
		# the ITL client sends requests through an already established socket connection, so config info like the port number and scheme don't exist
		return None

	def net_call(self, url, param_str):

		url_components = url.split('/')
		url_head = '/'.join(url_components[:3])
		endpoint = '/' + '/'.join(url_components[3:])

		call_ID = next(self.call_ID_gen)
		result_future = Future()
		self.pending_reqs[call_ID] = result_future

		logger.debug('RPC call to: %s for: %s call_ID: %s', self.sid, endpoint, call_ID)

		req_str = f'{call_ID}|{endpoint}|{param_str}'
		sio_send(partial(self.sio.emit, to=self.sid), 'rpc_request', req_str)

		return result_future.result()

	def disconnect_handler(self):

		# send a worker disconnect error back through each pending request
		for call_ID in self.pending_reqs:
			result_str = serialize(BaseException('WorkerDisconnect'))
			result_str = f'1|{result_str}'
			self.pending_reqs[call_ID].set_result(result_str)

@sio.event
def rpc_result(sid, return_str):
	global client_sid_map

	call_ID, result_str = return_str.split('|', 1)
	logger.debug('RPC response for call_ID: %s', call_ID)
	client = client_sid_map[sid]
	result_future = client.pending_reqs[call_ID]
	result_future.set_result(result_str)

@sio.event
def rpc_result_chunk(sid, res_str):
	global client_sid_map

	client = client_sid_map[sid]
	assembled = client.chunk_buffer.receive(res_str)

	if assembled is not None:
		call_ID, result_str = assembled.split('|', 1)
		logger.debug('received all chunks for call_ID: %s', call_ID)
		client.pending_reqs[call_ID].set_result(result_str)

@sio.event
def worker_header(sid, name):
	global client_sid_map
	client_sid_map[sid] = CloudClient(sio, sid, name)
	
@sio.event
def update_profile(sid, profile_str):
	global http_node, socket_node, client_sid_map
	logger.debug(f'update_profile {sid}')

	profile = deserialize(profile_str)

	tl_client = client_sid_map[sid]
	stub = axon.client.make_ServiceStub('ws://none:0000', tl_client, profile, stub_type=axon.stubs.SyncStub)
	
	http_node.add_child(tl_client.name, stub)
	# socket_node.add_child(tl_client.name, stub)

# created on the cloud/reflector side when an EdgeClient connects
class CloudWorker(AbstractTransportWorker):

	def __init__(self, sio, sid):
		super().__init__()

		self.chunk_buffer = ChunkBuffer()
		self.sio = sio
		self.sid = sid

		# for if an error means the worker must terminate
		self.terminal_error_future = Future()

	# handles chunking the response back to client
	def invoke_rpc_helper(self, req_str):
		call_ID, endpoint, param_str = req_str.split('|', 2)

		result_str = self.invoke_RPC(endpoint, param_str, in_parallel=True)

		try:
			sio_send(self.sio.emit, 'rpc_result', f'{call_ID}|{result_str}')

		except(BaseException):
			error = sys.exc_info()[1]
			self.terminal_error_future.set_result(error)

	def run(self):
		raise(self.terminal_error_future.result())

@sio.event
def rpc_request(sid, req_str):
	global worker_sid_map

	worker = worker_sid_map[sid]
	worker.invoke_rpc_helper(req_str)

@sio.event
def rpc_request_chunk(sid, event_str):
	global worker_sid_map

	worker = worker_sid_map[sid]
	assembled = worker.chunk_buffer.receive(event_str)

	if assembled is not None:
		worker.invoke_rpc_helper(assembled)

@sio.event
def client_header(sid):
	global worker_sid_map
	worker = CloudWorker(sio, sid)

	worker.serialize = null_serialize
	worker.deserialize = null_deserialize
	
	worker.rpcs = copy(http_node.tl.rpcs)
	worker_sid_map[sid] = worker

@sio.event
def connect(sid, e):
	logger.debug('New connection from: %s', sid)

@sio.event
def disconnect(sid):
	global http_node, client_sid_map

	if sid in client_sid_map:
		logger.debug('Worker %s disconnected', sid)
		client = client_sid_map[sid]

		http_node.remove_child(client.name)

		client.disconnect_handler()
		del client_sid_map[sid]

	if sid in worker_sid_map:
		del worker_sid_map[sid]

def run(endpoint='reflected_services', ws_port=5000, http_port=default_http_port):
	global http_node, socket_node, http_tl, logger

	if logger == None:
		init_logger()

	http_tl = transport.worker(http_port)
	tpe = ThreadPoolExecutor(axon.config.NUM_OPEN_REQS)

	http_tl.serialize = null_serialize
	http_tl.deserialize = null_deserialize

	http_thread = threading.Thread(target=http_tl.run, daemon=True)
	http_thread.start()
	time.sleep(0.5)

	http_node = axon.worker.ServiceNode({}, endpoint, tl=http_tl, executor=tpe)

	logger.debug('Reflector start')

	app = Flask(__name__)
	app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)
	app.run(host='0.0.0.0', port=ws_port)