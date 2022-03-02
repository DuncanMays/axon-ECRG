# the bit that listens idly and serves RPCs
# and executor is the thing that takes a function, and executes it in a thread/process and returns the result as response or even another HTTP req entirely

from .utils import deserialize, serialize, get_self_ip, overwrite
from .comms_wrappers import simplex_wrapper, duplex_wrapper
from .config import comms_config, default_rpc_config, default_service_config
from .inline_executor import InlineExecutor

from flask import Flask
from flask import request as route_req
from multiprocessing import Process
import threading
import inspect
import random
import string

# where the services being offered are stored
rpcs = []
# the ip address of the worker
ip_addr = get_self_ip()
# the app that listens for incomming http requests
app = Flask(__name__)
name = 'worker'
node_type = 'worker'

# a default route to serve up what rpcs this worker offers, and their configuration
@app.route('/_get_profile', methods=['GET'])
def _get_profile():
	global name, ip_addr, rpcs

	profile = {
		'name': name,
		'ip_addr': ip_addr,
		'rpcs': rpcs
	}

	return serialize(profile)

# a default route to kill the worker in case a bug blocks SIGINT
@app.route('/_kill', methods=['GET'])
def kill():
	func = route_req.environ.get('werkzeug.server.shutdown')

	if func is None:
		raise RuntimeError('Not running with the Werkzeug Server')

	func()
	return 'shutting down'

# a default route to provide basic info about the axon node, namely, that it's a worker
@app.route('/_type', methods=['GET'])
def _type():
	return node_type

# this returns the function that actually gets registered as a route in flask.
def get_route_fn(configuration, fn):
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

	try:
		executor = configuration['executor']
	except(KeyError):
		raise(KeyError('executor not specified in RPC configuration'))

	if (executor == 'inline'):
		executor = InlineExecutor
	elif (executor == 'Process'):
		executor = Process
	elif((executor == 'Thread')):
		executor = threading.Thread
	else:
		raise(BaseException('unrecognized executor configuration:', executor))

	wrapped_fn = comms_wrapper(fn, executor)

	return wrapped_fn

# this function returns a function which will be applied to functions which the caller wishes to turn into RPCs
def rpc(**configuration):
	# accepts options for the RPC, simplex/duplex, and running environment
	# sets up the function that registers the route

	# overwrites the default configuration with keys from caller input
	configuration = overwrite(default_rpc_config, configuration)

	# this is the function that will be applied to functions which the caller wishes to turn into RPCs
	# accepts a function, which it will wrap in an executor function depending on the configuration passed to rcp, this wrapped function will be registered as a route
	def init_rpc(fn):
		name = fn.__name__

		configuration['name'] = name
		rpcs.append(configuration)

		# wraps fn in the needed code to deserialize parameters from the request return its results, as well as run in a separate process/thread
		route_fn = get_route_fn(configuration, fn)
		# functions that flask registers as routes must have different names, even if they are registered at different endpoints. get_executor returns a function called 'wrapped_fn' every time, so we've got to change the name of the function here.
		# it is set to a random string firstly because the literal name of the function is arbitrary, but also because some services might have functions with the same names
		route_fn.__name__ = ''.join(random.choices(string.ascii_letters, k=10))
		# the endpoint of the route which exposes the function
		endpoint = '/'+configuration['endpoint_prefix']+name

		# registering the function as a route
		# print(endpoint)
		app.route(endpoint, methods=['POST'])(route_fn)

		return fn

	return init_rpc

# starts the web app
def init(wrkr_name='worker'):
	global name

	name = wrkr_name
	# the web application that will serve the services and rpcs as routes
	app.run(host='0.0.0.0', port=comms_config.worker_port, threaded=False)