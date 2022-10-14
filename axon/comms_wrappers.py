from .config import comms_config
from .utils import deserialize, serialize, POST
from .inline_executor import InlineExecutor, inline_lock

from flask import Flask
from flask import request as route_req
from multiprocessing import Process, Manager
from threading import Thread
import threading
import requests
import inspect
import sys
import asyncio
import traceback

# catches any errors in fn, and handles them properly
def error_wrapper(fn):

	def wrapped_fn(args, kwargs):
		return_object = {
			'errcode': 0,
			'result': None,
		}

		try:
			# execute the given function
			return_object['result'] = fn(*args, **kwargs)

		except:

			return_object['errcode'] = 1
			return_object['result'] = (traceback.format_exc(), sys.exc_info()[1])

		return return_object

	return wrapped_fn

def async_wrapper(fn):

	def wrapped_fn(params):
		return asyncio.run(fn(params))

	return wrapped_fn

# wraps fn in the code needed for simplex communication pattern
# adds code to deserialize parameters from the request and return its results through the response
mp_manager = Manager()
def simplex_wrapper(fn, executor):

	def wrapped_fn():

		result_holder = mp_manager.dict()

		# this function will run in an executor, will execute the RPC and return the result through a multiprocessing manager
		def wrk_fn(fn, params_str, result_holder):

			# deserializes parameters
			args, kwargs = deserialize(params_str)

			# if fn is a coroutine, it needs to be run with an event loop
			if inspect.iscoroutinefunction(fn): fn = async_wrapper(fn)

			# catches and returns any error
			fn = error_wrapper(fn)

			# runs the function
			return_object = fn(args, kwargs)

			result_holder['result'] = serialize(return_object)

		params_str = route_req.form['msg']

		# for now an executor means something like a thread or process, not a literal python executor. We'll use __call__ instead of submit
		fn_executor = executor(target=wrk_fn, args=(fn, params_str, result_holder))
		fn_executor.deamon = True
		fn_executor.start()

		fn_executor.join()

		return result_holder['result']

	return wrapped_fn



# wraps fn in the needed for duplex communication pattern
# adds code to deserialize parameters from the request and return its results through the a separate request
def duplex_wrapper(fn, executor):

	def wrapped_fn():

		# this function will run in a separate thread, will execute the RPC and return the result with a POST request
		def wrk_fn(fn, params_str, calling_ip):

			# deserializes parameters
			(call_info, args, kwargs) = deserialize(params_str)

			# the info needed to return the result
			call_id = call_info['id']
			rvl_port = call_info['rvl_port']

			# if fn is a coroutine, it needs to be run with an event loop
			if inspect.iscoroutinefunction(fn): fn = async_wrapper(fn)

			# catches and returns any error
			fn = error_wrapper(fn)

			# runs the function
			return_object = fn(args, kwargs)

			# returns the result via a POST request
			url = 'http://'+calling_ip+':'+str(rvl_port)+'/_return_value_linker'
			data = {'result': serialize(return_object), 'id': serialize(call_id)}
			
			# TODO: this should be wrapped in a try/except for the case when the caller isn't listenning, this is a common case since a simplex stub would start the RPC but not listen for a response
			x=requests.post(url=url, data=data)

		params_str = route_req.form['msg']
		calling_ip = route_req.remote_addr

		# because flask, and WSGI servers in general, cannot schedule code to execute after a route completes, inline duplex RPCs would have to send the returning request before the calling request completes
		# to prevent this, we must run the RPC in a separate thread, and to preserve synchronous bahavior, we must use a threadlock with other inline RPCs. This will ensure no two inline RPCs are executing at the same time.
		fn_executor = None
		if(executor == InlineExecutor):

			def inline_lock_fn(fn, params_str, calling_ip):
				with inline_lock:
					result = wrk_fn(fn, params_str, calling_ip)

				return result

			fn_executor = Thread(target=inline_lock_fn, args=(fn, params_str, calling_ip))
		else:
			fn_executor = executor(target=wrk_fn, args=(fn, params_str, calling_ip))

		fn_executor.deamon = True
		fn_executor.start()

		return serialize('duplex')

	return wrapped_fn