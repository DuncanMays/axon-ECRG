from axon.serializers import deserialize, serialize

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

	return serialize(result)