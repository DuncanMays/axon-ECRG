from .config import comms_config
from .utils import deserialize, serialize, POST

from flask import Flask
from flask import request as route_req
from multiprocessing import Process, Manager
import threading
import requests
import inspect
import sys
import asyncio

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
			# catch and return all errors
			error_info = sys.exc_info()
			error_class = error_info[0]
			error_instance = error_info[1]

			return_object['errcode'] = 1
			return_object['result'] = (error_class, error_instance)

		return return_object

	return wrapped_fn

def async_wrapper(fn):

	def wrapped_fn(params):
		return asyncio.run(fn(params))

	return wrapped_fn

# wraps fn in the needed for simplex communication pattern
# adds code to deserialize parameters from the request and return its results through the response
def simplex_wrapper(fn, executor):

	def wrapped_fn():

		mp_manager = Manager()
		result_holder = mp_manager.dict()

		# this function will run in a separate thread, will execute the RPC and return the result with a POST request
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
			data = {'msg': serialize((call_id, return_object))}
			requests.post(url=url, data=data)

		params_str = route_req.form['msg']
		calling_ip = route_req.remote_addr

		fn_executor = executor(target=wrk_fn, args=(fn, params_str, calling_ip))
		fn_executor.deamon = True
		fn_executor.start()

		return serialize('duplex')

	return wrapped_fn