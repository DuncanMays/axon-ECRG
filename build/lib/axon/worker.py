# the bit that listens idly and serves RPCs
# and executor is the thing that takes a function, and executes it in a thread/process and returns the result as response or even another HTTP req entirely

from .utils import deserialize, serialize, sign_in, sign_out, get_self_ip
from .comms_wrappers import simplex_wrapper, duplex_wrapper
from .config import comms_config, default_rpc_config

from flask import Flask
from flask import request as route_req
from multiprocessing import Process
import threading
import sys
import signal
import inspect

# stops flask from outputting starting message
# cli = sys.modules['flask.cli']
# cli.show_server_banner = lambda *x: 'hello there'

# # stops flask from printing to console when it fulfills a request
# import logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)
# log.disabled = True

# where the rpcs being offered are stored
rpcs = []
# the ip address of the worker
ip_addr = get_self_ip()
# the app that listens for incomming http requests
app = Flask(__name__)
# app.logger.disabled = True

# a default route to serve up what rpcs this worker offers, and their configuration
@app.route('/_get_profile', methods=['GET'])
def _get_profile():
	global rpcs

	profile = {
		'ip_addr': ip_addr,
		'rpcs': rpcs
	}

	return serialize(profile)

# accepts two dicts, target and source
# in any shared keys between the two will be overwritten to source's value, and any keys in source will be copied to target, with thei values
def overwrite(target, source):

	for key in source:
		target[key] = source[key]

	return target

def get_executor(configuration, fn):
	# wraps fn in two layers
	# the outer layer handles the communication pattern, being either simplex or duplex
	# the inner layer handles the execution environment, be that a thread or a process

	comms_pattern = configuration['comms_pattern']
	comms_wrapper = None
	if (comms_pattern == 'simplex'):
		comms_wrapper = simplex_wrapper
	elif (comms_pattern == 'duplex'):
		comms_wrapper = duplex_wrapper
	else:
		raise BaseException('unrecognized comms_pattern: '+str(comms_pattern))

	executor = configuration['executor']
	if (executor == 'Process'):
		executor = Process
	elif((executor == 'Thread')):
		executor = threading.Thread

	wrapped_fn = comms_wrapper(fn, executor)

	return wrapped_fn

# this function returns a function which will be applied to functions which the caller wishes to turn into RPCs
def rpc(**configuration):
	# accepts options for the RPC, simplex/duplex, and running environment
	# sets up the function that registers the route

	configuration = overwrite(default_rpc_config, configuration)

	# this is the function that will be applied to functions which the caller wishes to turn into RPCs
	# accepts a function, which it will wrap in an executor function depending on the configuration passed to rcp, this wrapped function will be registered as a route
	def init_rpc(fn):
		name = fn.__name__ 
		endpoint = '/'+name	

		rpc_desc = {
			'configuration': configuration,
			'name': name,
			'signature': inspect.signature(fn)
		}
		rpcs.append(rpc_desc)

		# wraps fn in the needed code to deserialize parameters from the request return its results, as well as run in a separate process/thread
		route_fn = get_executor(configuration, fn)
		# functions that flask registers as routes must have different names, even if they are registered at different endpoints. get_executor returns a function called 'wrapped_fn' every time, so we've got to change the name of the function here
		route_fn.__name__ = name

		# registering the function as a route
		app.route(endpoint, methods=['POST'])(route_fn)

		return fn

	return init_rpc

# gracefully kills the worker
def teardown(frame, file):
	sign_out()
	exit()

signal.signal(signal.SIGINT, teardown)

# starts the web app
def init():
	sign_in()
	# the web application that will serve the rpcs as routes
	app.run(host='0.0.0.0', port=comms_config.worker_port)