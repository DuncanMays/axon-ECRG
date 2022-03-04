# the bit that listens idly and serves RPCs
# and executor is the thing that takes a function, and executes it in a thread/process and returns the result as response or even another HTTP req entirely

from .utils import deserialize, serialize, get_self_ip, overwrite
from .comms_wrappers import simplex_wrapper, duplex_wrapper
from .config import comms_config, default_rpc_config, default_service_config
from .inline_executor import InlineExecutor

from flask import Flask
from flask import request as route_req
from multiprocessing import Process
from copy import copy
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
		app.route(endpoint, methods=['POST'])(route_fn)

		return fn

	return init_rpc

class ServiceNode():

	def __init__(self, subject, name, **configuration):

		self.subject = subject
		self.name = name
		self.children = {}

		self.configuration = overwrite(default_service_config, configuration)

		# iterates over members and either registers them as RPCs or recursively turns them into ServiceNodes
		# for key, member in self.subject.__dict__.items():
		for key in dir(self.subject):
			member = getattr(self.subject, key)

			# if the member is callable, make it an RPC
			if callable(member):
				self.init_RPC(key, member)

			# else
			elif hasattr(member, '__dict__'):
				self.init_child(key, member)

		# we now register a GET route at the ServiceNode's endpoint to expose its profile
		
		# the function that will be exposed as a route
		def get_profile_str():
			profile = self.get_profile()
			return serialize(profile)

		# functions that flask registers as routes must have different names, even if they are registered at different endpoints, so we've got to change the name of the function here.
		# it is set to a random string firstly because the literal name of the function is arbitrary, but also because some services might have functions with the same names
		get_profile_str.__name__ = ''.join(random.choices(string.ascii_letters, k=10))
		endpoint = '/'+self.configuration['endpoint_prefix']+self.name

		app.route(endpoint, methods=['GET'])(get_profile_str)

	def init_child(self, key, child):
		child_config = copy(self.configuration)
		child_config['endpoint_prefix'] += str(self.name)+'/'

		child = ServiceNode(child, key, **child_config)
		self.children[key] = child

	def init_RPC(self, key, fn):
		child_config = copy(self.configuration)
		child_config['endpoint_prefix'] += str(self.name)+'/'

		# make it an RPC
		make_rpc = rpc(**child_config)
		make_rpc(fn)
		# remember the configuration
		self.children[key] = child_config

	# returns the ServiceNode's profile, with information that's common to all children of the ServiceNode, like its IP address
	def get_root_profile(self):
		profile = self.get_profile()

		root_profile['profile'] = profile
		root_profile['ip_addr'] = self.ip_addr
		root_profile['name'] = self.name
		root_profile['endpoint_prefix'] = self.configuration['endpoint_prefix']
		# this is a flag attribute that lets a ServiceStub know that a dict is a root profile for a ServiceNode
		root_profile['__profile_flag__'] = False

		return root_profile

	# returns a JSON serializable dict tree with leaves of RPC configuration dicts
	def get_profile(self):
		
		profile = {}

		# this is a flag attribute that lets a ServiceStub know that a dict is a profile for a ServiceNode, not a configuration dict for an RPC
		profile['__profile_flag__'] = True

		for key in self.children.keys():
			child = self.children[key]

			# if the child is itself a ServiceNode, recursively get the profiles of its attributes
			if isinstance(child, ServiceNode):
				profile[key] = child.get_profile()

			# if the attribute is an RPC, the profile element is its configuration
			else:
				profile[key] = child

		return profile

# starts the web app
def init(wrkr_name='worker'):
	global name

	name = wrkr_name
	# the web application that will serve the services and rpcs as routes
	app.run(host='0.0.0.0', port=comms_config.worker_port, threaded=False)