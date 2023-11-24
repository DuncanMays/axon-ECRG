# the bit that listens idly and serves RPCs
# and executor is the thing that takes a function, and executes it in a thread/process and returns the result as response or even another HTTP req entirely

from .utils import deserialize, serialize, get_self_ip, overwrite
from .comms_wrappers import simplex_wrapper
from .config import comms_config, default_rpc_config, default_service_config, default_service_depth
from .inline_executor import InlineExecutor

# from .transport_worker import register_RPC, _init
from .comms_wrappers import async_wrapper, error_wrapper

from flask import Flask
from flask import request as route_req
from multiprocessing import Process
from copy import copy
import threading
import inspect
import random
import string

# the ip address of the worker
ip_addr = get_self_ip()
# the app that listens for incomming http requests
app = Flask(__name__)
name = 'worker'

# a default route to serve up what rpcs this worker offers, and their configuration
@app.route('/_get_profile', methods=['GET'])
def _get_profile():
	global name, ip_addr

	service_profiles = {}
	for key in registered_ServiceNodes:
		service_profiles[key] = registered_ServiceNodes[key].get_profile()

	profile = {
		'name': name,
		'ip_addr': ip_addr,
		'rpcs': RPC_node.get_profile(),
		'services': service_profiles,
	}

	return serialize(profile)

# this returns the function that actually gets registered as a route in flask.
def get_route_fn(configuration, fn):
	# wraps fn in two layers
	# the outer layer handles the communication pattern, being either simplex or duplex
	# the inner layer handles the execution environment, be that a thread or a process

	comms_wrapper = simplex_wrapper

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
def make_RPC_skeleton(**configuration):
	# accepts options for the RPC, simplex/duplex, and running environment
	# sets up the function that registers the route

	# overwrites the default configuration with keys from caller input
	configuration = overwrite(default_rpc_config, configuration)

	# this is the function that will be applied to functions which the caller wishes to turn into RPCs
	# accepts a function, which it will wrap in an executor function depending on the configuration passed to rcp, this wrapped function will be registered as a route
	def init_rpc(fn):

		if not 'name' in configuration:
			configuration['name'] = fn.__name__

		# wraps fn in the needed code to deserialize parameters from the request return its results, as well as run in a separate process/thread
		route_fn = get_route_fn(configuration, fn)
		# functions that flask registers as routes must have different names, even if they are registered at different endpoints. get_executor returns a function called 'wrapped_fn' every time, so we've got to change the name of the function here.
		# it is set to a random string firstly because the literal name of the function is arbitrary, but also because some services might have functions with the same names
		route_fn.__name__ = ''.join(random.choices(string.ascii_letters, k=10))
		# the endpoint of the route which exposes the function
		endpoint = '/'+configuration['endpoint_prefix']+configuration['name']

		# registering the function as a route
		app.route(endpoint, methods=['POST'])(route_fn)

		return fn

	return init_rpc

def register_RPC(fn, **configuration):

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
	print(endpoint)
	app.route(endpoint, methods=['POST'])(route_fn)

registered_ServiceNodes = {}

def register_ServiceNode(subject, name, depth=default_service_depth, **configuration):

	s = ServiceNode(subject, name, depth=default_service_depth, **configuration)
	registered_ServiceNodes[name] = s
	return s

class ServiceNode():

	def __init__(self, subject, name, depth=default_service_depth, **configuration):
		self.subject = subject
		self.name = name
		self.children = {}
		self.depth = depth

		self.configuration = overwrite(default_service_config, configuration)

		# iterates over members and either registers them as RPCs or recursively turns them into ServiceNodes
		# for key, member in self.subject.__dict__.items():
		for key in dir(self.subject):

			# dir calls the overwritable __dir__ function on self.subject. This means it's unreliable in some cases, since developers can specify what it returns.
			# this can mean the attribute is listed but does not exist, or even that calling the attribute throws an error
			try:
				if not hasattr(self.subject, key):
					continue

			except(BaseException):
				# sometimes merely accessing an attribute can throw an error
				continue

			member = getattr(self.subject, key)

			if (key == '__call__'):
				# Any member accessed via __call__ attribute is represented in profile by an RPC config. This means that objects stored on __call__ attributes will not be represented in profile
				self.init_RPC(key, member)
			
			elif hasattr(member, '__dict__'):
				# Any member with a __dict__ attribute gets a profile, provided it as not been accessed via __call__
				self.add_child(key, member)

			elif hasattr(member, '__call__'):
				# Any member with a __call__ attribute but no __dict__ attribute is represented in profile by an RPC config
				self.init_RPC(key, member)

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

	def add_child(self, key, child, **child_config):
		# limits recursion to a depth parameter
		if (self.depth <= 0): return

		# The child config overwrites the parent's config, meaning by default children inherit configuration from their parents
		child_config = overwrite(self.configuration, child_config)

		# the child's endpoint_prefix is the parent's prefix plus / and the child's name
		child_config['endpoint_prefix'] += str(self.name)+'/'

		# create a ServiceNode out of it and register it as a child
		child = ServiceNode(child, key, depth=self.depth-1, **child_config)
		self.children[key] = child

	def init_RPC(self, key, fn):
		child_config = copy(self.configuration)
		child_config['endpoint_prefix'] += str(self.name)+'/'
		child_config['name'] = key

		# make it an RPC
		
		make_rpc = make_RPC_skeleton(**child_config)
		make_rpc(fn)

		# register_RPC(fn, **child_config)

		# remember the configuration
		self.children[key] = child_config

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

# a ServiceNode that holds all RPCs associated by this worker instance
RPC_node = ServiceNode(object(), default_rpc_config['endpoint_prefix'])

# the RPC decorator adds the associated function to the RPC_node ServiceNode
def rpc(**configuration):
	def add_to_RPC_node(fn):
		RPC_node.add_child(fn.__name__, fn, **configuration)

	return add_to_RPC_node

# starts the web app
def init(wrkr_name='worker'):
	global name

	name = wrkr_name
	# the web application that will serve the services and rpcs as routes
	app.run(host='0.0.0.0', port=comms_config.worker_port, threaded=False)