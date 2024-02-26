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

class HTTPTransportWorker():

	def __init__(self, port):
		# all RPCs registered with this TL are stored here in this dict
		self.rpcs = {}

		# removes the startup text
		cli = sys.modules['flask.cli']
		cli.show_server_banner = lambda *x: None
		log = logging.getLogger('werkzeug')
		log.disabled = True

		# the app that listens for incomming http requests
		self.app = Flask('HTTPTransportWorker')	
		self.port = port

		# the route that listens for incomming RPC requests
		@self.app.route('/', defaults={'path': ''}, methods=['POST'])
		@self.app.route('/<path:path>', methods=['POST'])
		def catch_all(path):
			path = '/'+path
			(fn, executor) = self.rpcs[path]

			param_str = route_req.form['msg']
			future = executor.submit(invoke_RPC, fn, param_str)
			return future.result()

	def run(self):
		self.app.run(host='0.0.0.0', port=self.port)

	def register_RPC(self, fn, endpoint, executor):

		if isinstance(executor, PPE):
			fn = cloudpickle.dumps(fn)

		self.rpcs[endpoint] = (fn, executor)