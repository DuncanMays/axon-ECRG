from .serializers import deserialize, serialize

from flask import Flask
from flask import request as route_req
from concurrent.futures import ProcessPoolExecutor as PPE
from threading import Thread, Lock

import sys
import logging
import random
import string
import cloudpickle
import traceback
import inspect
import pickle
import asyncio

loop, event_loop_thread = None, None
def start_event_loop_thread():
	global loop, event_loop_thread
	loop = asyncio.new_event_loop()
	asyncio.set_event_loop(loop)
	event_loop_thread = Thread(target=loop.run_forever, daemon=True)
	event_loop_thread.start()

inline_lock = Lock()
def invoke_RPC(target_fn, param_str, in_parallel=True):
	global loop, event_loop_thread

	if isinstance(target_fn, bytes) or isinstance(target_fn, str):
		target_fn = pickle.loads(target_fn)

	args, kwargs = deserialize(param_str)

	return_object = {
		'errcode': 0,
		'result': None,
	}

	try:
		result = None

		if not in_parallel:
			with inline_lock:
				result = target_fn(*args, **kwargs)
		else:
			result = target_fn(*args, **kwargs)

		if inspect.iscoroutine(result):
			if (event_loop_thread == None) or not (event_loop_thread.is_alive()):
				start_event_loop_thread()
				
			result = asyncio.run_coroutine_threadsafe(result, loop).result()

		return_object['result'] = result

	except:
		return_object['errcode'] = 1
		return_object['result'] = (traceback.format_exc(), sys.exc_info()[1])

	return serialize(return_object)

cclass SocketTransportWorker():

	def __init__(self, port):
		self.port = port
		self.RPCs = {}

	def run(self):
		with s.serve(self.call_RPC, '127.0.0.1', self.port) as server:
			server.serve_forever()

	def call_RPC(websocket):
		endpoint, param_str = websocket.recv()
		return self.RPCs[endpoint](param_str)

	def register_RPC(self, fn, **configuration):

		if not 'name' in configuration:
			configuration['name'] = fn.__name__

		executor = configuration['executor']

		if isinstance(executor, PPE):
			fn = cloudpickle.dumps(fn)

		def route_fn(param_str):
			future = executor.submit(invoke_RPC, fn, param_str)
			websocket.send(future.result())

		endpoint = '/'+configuration['endpoint_prefix']+configuration['name']
		
		self.RPCs[endpoint] = route_fn