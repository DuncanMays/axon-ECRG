import sys
sys.path.append('..')

import axon
import time
import threading
import socketio
import logging
import psutil
import random

from concurrent.futures import Future
from threading import Timer
from flask import Flask

from axon.serializers import serialize, deserialize
from axon.transport_client import req_executor, error_handler, AsyncResultHandle
from axon.config import transport, default_service_config
from axon.chunking import send_in_chunks, recv_chunks
from axon.HTTP_transport.config import port as default_http_port
from axon.utils import get_ID_generator
from axon.reflector import config as refl_config
from axon.transport_client import AbstractTransportClient

sio = socketio.Server(async_mode='threading')
reflector_node = None
client_sid_map = {}

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
		self.sio = sio
		self.sid = sid
		self.name = name
		self.pending_reqs = {}
		self.chunk_buffers = {}
		self.call_ID_gen = get_ID_generator()

	def get_config(self):
		# the ITL client sends requests through an already established socket connection, so config info like the port number and scheme don't exist
		return None

	def call_rpc(self, url, args, kwargs):

		url_components = url.split('/')
		url_head = '/'.join(url_components[:3])
		endpoint = '/' + '/'.join(url_components[3:])

		call_ID = next(self.call_ID_gen)
		result_future = Future()
		self.pending_reqs[call_ID] = result_future

		logger.debug('RPC call to: %s for: %s call_ID: %s', self.sid, endpoint, call_ID)
		self.sio.emit('rpc_request', to=self.sid, data=f'{call_ID}|{endpoint}|{serialize((args, kwargs))}')
		
		result_str = result_future.result()
		result_str = error_handler(result_str)
		return deserialize(result_str)

	def disconnect_handler(self):

		# send a worker disconnect error back through each pending request
		for call_ID in self.pending_reqs:
			result_str = serialize(('The worker closed connection before responding to RPC', BaseException('WorkerDisconnect')))
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
def connect(sid, e):
	logger.debug('New connection from: %s', sid)

@sio.event
def disconnect(sid):
	global reflector_node, client_sid_map

	logger.debug('Worker %s disconnected', sid)
	client = client_sid_map[sid]

	reflector_node.remove_child(client.name)
	client.disconnect_handler()
	del client_sid_map[sid]

@sio.event
def worker_header(sid, name):
	global client_sid_map
	client_sid_map[sid] = ITL_Client(sio, sid, name)
	
@sio.event
def update_profile(sid, profile_str):
	global reflector_node, client_sid_map
	logger.debug(f'update_profile {sid}')

	profile = deserialize(profile_str)

	itl = client_sid_map[sid]
	stub = axon.client.make_ServiceStub('ws://none:0000', itl, profile, stub_type=axon.stubs.SyncStub)
	reflector_node.add_child(itl.name, stub)

def run(endpoint='reflected_services', ws_port=5000, http_port=default_http_port):
	global reflector_node, http_tl, logger

	if logger == None:
		init_logger()

	http_tl = transport.worker(http_port)

	http_thread = threading.Thread(target=http_tl.run, daemon=True)
	http_thread.start()
	time.sleep(0.5)

	# reflector_node = axon.worker.service({}, endpoint, tl=http_tl)
	reflector_node = axon.worker.ServiceNode({}, endpoint, tl=http_tl)

	logger.debug('Reflector start')

	app = Flask(__name__)
	app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)
	app.run(host='0.0.0.0', port=ws_port)