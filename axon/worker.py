# the bit that listens idly and serves RPCs
# and executor is the thing that takes a function, and executes it in a thread/process and returns the result as response or even another HTTP req entirely

from .utils import deserialize, serialize, get_self_ip, overwrite
from .config import comms_config, default_rpc_config, default_service_config, default_service_depth

from flask import Flask
from flask import request as route_req
from copy import copy
import inspect
import random
import string
import traceback
import sys
import logging

# the ip address of the worker
ip_addr = get_self_ip()
cli = sys.modules['flask.cli']
cli.show_server_banner = lambda *x: None
log = logging.getLogger('werkzeug')
log.disabled = True
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

		executor = configuration['executor']

		# print(executor)
		# result = executor.submit(target_fn, args, kwargs)

		# return_val = result.result()

		return_val = target_fn(args, kwargs)

		return serialize(return_val)

	route_fn.__name__ = ''.join(random.choices(string.ascii_letters, k=10))
	endpoint = '/'+configuration['endpoint_prefix']+configuration['name']
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

		register_RPC(fn, **child_config)

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
				child_copy = copy(child)
				del child_copy['executor']
				profile[key] = child_copy

		return profile

# a ServiceNode that holds all RPCs associated by this worker instance
RPC_node = ServiceNode(object(), default_rpc_config['endpoint_prefix'])

# the RPC decorator adds the associated function to the RPC_node ServiceNode
def rpc(**configuration):
	def add_to_RPC_node(fn):
		RPC_node.add_child(fn.__name__, fn, **configuration)

	return add_to_RPC_node

# starts the web app
def init(wrkr_name='worker', port=comms_config.worker_port):
	global name

	name = wrkr_name
	# the web application that will serve the services and rpcs as routes
	app.run(host='0.0.0.0', port=port, threaded=True)