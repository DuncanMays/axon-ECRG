import sys
sys.path.append('..')

import axon
import time
import threading
import socketio
import logging

from concurrent.futures import Future, ThreadPoolExecutor
from flask import Flask
from math import ceil
from copy import copy

from axon.serializers import serialize, deserialize
from axon.transport_client import AbstractTransportClient
from axon.transport_worker import AbstractTransportWorker
from axon.config import transport
from axon.HTTP_transport.config import port as default_http_port
from axon.utils import get_ID_generator
from axon.reflector import config as refl_config

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

# this class extends the client and encapsulates the connection with a worker
class ITL_Client(AbstractTransportClient):

	def __init__(self, sio, sid, name):
		super().__init__()
		
		self.sio = sio
		self.sid = sid
		self.name = name
		self.pending_reqs = {}
		self.chunk_buffers = {}
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

		chunk_size = 100_000

		req_str = f'{call_ID}|{endpoint}|{param_str}'

		if (len(req_str) < chunk_size):
			self.sio.emit('rpc_request', to=self.sid, data=req_str)

		else:
			num_chunks = ceil(len(req_str)/chunk_size)

			for i in range(num_chunks):
				chunk_str = req_str[ chunk_size*i : chunk_size*(i+1) ]
				self.sio.emit('rpc_request_chunk', to=self.sid, data=f'{str(i)}|{str(num_chunks)}|{call_ID}|{chunk_str}')		
		
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

	chunk_num, num_chunks, call_ID, chunk_str = res_str.split('|', 3)
	logger.debug('RPC response chunk %s for call_ID: %s', chunk_num, call_ID)

	chunk_obj = {
		'chunk_str': chunk_str,
		'chunk_num': int(chunk_num)
	}

	client = client_sid_map[sid]

	if (call_ID in client.chunk_buffers):
		client.chunk_buffers[call_ID].append(chunk_obj)

	else :
		client.chunk_buffers[call_ID] = [chunk_obj]

	if (len(client.chunk_buffers[call_ID]) == int(num_chunks)):

		chunks = client.chunk_buffers[call_ID]
		chunks.sort(key=lambda x: x['chunk_num'])
		chunk_strs = [b['chunk_str'] for b in chunks]
		result_str = ''.join(chunk_strs)

		result_future = client.pending_reqs[call_ID]
		result_future.set_result(result_str)

		logger.debug('recieved all chunks for call_ID: %s', call_ID)
		del client.chunk_buffers[call_ID]

@sio.event
def worker_header(sid, name):
	global client_sid_map
	client_sid_map[sid] = ITL_Client(sio, sid, name)
	
@sio.event
def update_profile(sid, profile_str):
	global http_node, socket_node, client_sid_map
	logger.debug(f'update_profile {sid}')

	profile = deserialize(profile_str)

	tl_client = client_sid_map[sid]
	stub = axon.client.make_ServiceStub('ws://none:0000', tl_client, profile, stub_type=axon.stubs.SyncStub)
	
	http_node.add_child(tl_client.name, stub)
	# socket_node.add_child(tl_client.name, stub)

# this class extends the client and encapsulates the connection with a client
class ITL_Worker(AbstractTransportWorker):

	def __init__(self, sio, sid):
		super().__init__()

		self.chunk_buffers = {}
		self.sio = sio
		self.sid = sid

		# for if an error means the worker must terminate
		self.terminal_error_future = Future()

	# handles chunking the response back to client
	def invoke_rpc_helper(self, req_str):
		call_ID, endpoint, param_str = req_str.split('|', 3)

		result_str = self.invoke_RPC(endpoint, param_str, in_parallel=True)

		chunk_size = 100_000

		try:
			if (len(result_str) < chunk_size):
				self.sio.emit('rpc_result', data=f'{call_ID}|{result_str}')

			else:
				num_chunks = ceil(len(result_str)/chunk_size)

				for i in range(num_chunks):
					chunk_str = result_str[ chunk_size*i : chunk_size*(i+1) ]
					self.sio.emit('rpc_result_chunk', data=f'{str(i)}|{str(num_chunks)}|{call_ID}|{chunk_str}')

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
	chunk_num, num_chunks, call_ID, chunk_str = event_str.split('|', 3)

	chunk_obj = {
		'chunk_str': chunk_str,
		'chunk_num': int(chunk_num)
	}

	if (call_ID in worker.chunk_buffers):
		worker.chunk_buffers[call_ID].append(chunk_obj)

	else :
		worker.chunk_buffers[call_ID] = [chunk_obj]

	if (len(worker.chunk_buffers[call_ID]) == int(num_chunks)):

		chunks = worker.chunk_buffers[call_ID]
		chunks.sort(key=lambda x: x['chunk_num'])
		chunk_strs = [b['chunk_str'] for b in chunks]
		req_str = ''.join(chunk_strs)

		worker.invoke_rpc_helper(req_str)

@sio.event
def client_header(sid):
	global worker_sid_map
	worker = ITL_Worker(sio, sid)

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