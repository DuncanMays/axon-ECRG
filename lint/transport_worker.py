from .utils import serialize, deserialize, overwrite
from .config import default_rpc_config, comms_config

from flask import Flask
from flask import request as route_req
import inspect
import random
import string

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

def register_RPC(app, fn, **configuration):

	configuration = overwrite(default_rpc_config, configuration)
	if not 'name' in configuration:
		configuration['name'] = fn.__name__

	def route_fn():

		# fn needs to be assigned to a variable in the function scope because otherwise assignment statements,: fn = fn, will throw fn is referenced before assignment
		target_fn = fn

		args, kwargs = deserialize(route_req.form['msg'])

		if inspect.iscoroutinefunction(target_fn): target_fn = async_wrapper(target_fn)

		target_fn = error_wrapper(target_fn)

		result = target_fn(args, kwargs)

		return serialize(result)

	route_fn.__name__ = ''.join(random.choices(string.ascii_letters, k=10))
	endpoint = '/'+configuration['endpoint_prefix']+configuration['name']
	# print(endpoint)
	app.route(endpoint, methods=['POST'])(route_fn)

# def rpc(**configuration):
	
# 	def inner_rpc(fn):
# 		register_RPC(fn, **configuration)

# 	return inner_rpc

# starts the web app
def _init(wrkr_name='worker'):

	global name

	name = wrkr_name
	# the web application that will serve the services and rpcs as routes
	app.run(host='0.0.0.0', port=comms_config.worker_port, threaded=False)