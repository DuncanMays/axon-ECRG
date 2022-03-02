from .utils import overwrite
from .config import default_service_config, default_rpc_config
from .worker import rpc

class ServiceNode():

	def __init__(self, subject, name, **configuration):

		self.subject = subject
		self.name = name
		self.configuration = configuration
		self.children = {}

		configuration = overwrite(default_service_config, configuration)

		# iterates over members and either registers them as RPCs or recursively turns them into ServiceNodes
		# for key, member in self.subject.__dict__.items():
		for key in dir(self.subject):
			member = getattr(self.subject, key)

			# if the member is callable, make it an RPC
			if callable(member):
				# make it an RPC
				make_rpc = rpc(**configuration)
				make_rpc(member)
				# remember the configuration
				self.children[key] = configuration

			# if the member is itself a class, recursively turn it into a ServiceNode
			elif hasattr(member, '__dict__'):
				child_config = overwrite(configuration, {'endpoint_prefix': configuration['endpoint_prefix']+key+'/'})
				child = ServiceNode(member, key, **child_config)
				self.children[key] = child

	# returns a JSON serializable dict tree with leaves of RPC configuration dicts
	def get_profile(self):
		
		profile = {}

		for key in self.children.keys():
			child = self.children[key]

			# if the child is itself a ServiceNode, recursively get the profiles of its attributes
			if isinstance(child, ServiceNode):
				profile[key] = child.get_profile()

			# if the attribute is an RPC, the profile element is its configuration
			else:
				profile[key] = child

		return profile