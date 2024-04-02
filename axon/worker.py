# the bit that listens idly and serves RPCs
# and executor is the thing that takes a function, and executes it in a thread/process and returns the result as response or even another HTTP req entirely

from .utils import overwrite
from .config import comms_config, default_rpc_endpoint, default_service_config, default_service_depth
from .transport_worker import HTTPTransportWorker

from copy import copy
from threading import Thread
from time import sleep

import pickle, cloudpickle
import asyncio

transport_layers = set()

def _get_profile():

	service_profiles = {}
	dtl = default_service_config['tl']
	for key in registered_ServiceNodes:
		tl = registered_ServiceNodes[key].tl
		if (dtl == tl):
			service_profiles[key] = registered_ServiceNodes[key].get_profile()

	profile = {
		'rpcs': RPC_node.get_profile(),
		'services': service_profiles,
	}

	return profile

registered_ServiceNodes = {}

def register_ServiceNode(subject, name, depth=default_service_depth, **configuration):

	s = ServiceNode(subject, name, depth=depth, **configuration)
	registered_ServiceNodes[name] = s
	return s

class ServiceNode():

	def __init__(self, subject, name, depth=default_service_depth, **configuration):
		self.subject = subject
		self.name = name
		self.children = {}
		self.depth = depth

		self.configuration = overwrite(default_service_config, configuration)
		self.tl = self.configuration['tl']

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

		# we now register an RPC at the ServiceNode's endpoint to expose its profile
		# self.tl.register_RPC(self.get_profile, name=self.name, executor=default_service_config['executor'], endpoint_prefix=self.configuration['endpoint_prefix'])
		profile_endpoint = f"{self.configuration['endpoint_prefix']}/{self.name}"
		self.tl.register_RPC(self.get_profile, profile_endpoint, default_service_config['executor'])
		transport_layers.add(self.tl)

	def remove_child(self, child_key):

		child = self.children[child_key]

		if isinstance(child, ServiceNode):
			# remove all grandchildren
			grand_child_keys = list(child.children.keys())
			for grand_child_key in grand_child_keys:

				if (grand_child_key == '__call__'):
					endpoint = f"{self.configuration['endpoint_prefix']}/{self.name}/{child_key}/{grand_child_key}"
					self.tl.deregister_RPC(endpoint)

				else:
					child.remove_child(grand_child_key)

		# deregisters the child's profile endpoint
		profile_endpoint = f"{self.configuration['endpoint_prefix']}/{self.name}/{child_key}"
		self.tl.deregister_RPC(profile_endpoint)

		del self.children[child_key]

	def add_child(self, key, child, **child_config):
		# limits recursion to a depth parameter
		if (self.depth <= 0): return

		# The child config overwrites the parent's config, meaning by default children inherit configuration from their parents
		child_config = overwrite(self.configuration, child_config)

		# the child's endpoint_prefix is the parent's prefix plus / and the child's name
		child_config['endpoint_prefix'] += '/'+str(self.name)

		# create a ServiceNode out of it and register it as a child
		child = ServiceNode(child, key, depth=self.depth-1, **child_config)
		self.children[key] = child
		return child

	def init_RPC(self, key, fn):

		tl = self.configuration['tl']
		endpoint = f"{self.configuration['endpoint_prefix']}/{self.name}/{key}"

		# this dict will be sent back with the profile to client
		child_config = {
			'endpoint_prefix': self.configuration['endpoint_prefix'] +'/'+ str(self.name),
			'name': key,
			'executor': self.configuration['executor']
		}

		tl.register_RPC(fn, endpoint, self.configuration['executor'])

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
				
				# if the child uses a different transport layer, ignore it
				if (self.tl != child.tl):
					continue

				profile[key] = child.get_profile()

			# if the attribute is an RPC, the profile element is its configuration
			else:
				child_copy = copy(child)
				del child_copy['executor']
				profile[key] = child_copy

		return profile

# a ServiceNode that holds all RPCs associated by this worker instance
RPC_node = ServiceNode(object(), default_rpc_endpoint)

# the RPC decorator adds the associated function to the RPC_node ServiceNode
def rpc(**configuration):
	def add_to_RPC_node(fn):
		RPC_node.add_child(fn.__name__, fn, **configuration)
		return fn

	return add_to_RPC_node

def init(tl=default_service_config['tl']):

	profile_endpoint = f"{default_service_config['endpoint_prefix']}/_get_profile"
	tl.register_RPC(_get_profile, profile_endpoint, default_service_config['executor'])

	tl_threads = []
	for t in transport_layers:
		tl_thread = Thread(target=t.run, daemon=True)
		tl_thread.start()
		tl_threads.append(tl_thread)

	while True:
		sleep(1000_000)