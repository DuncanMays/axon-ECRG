from .utils import overwrite
from .config import default_service_config, default_rpc_config
from .worker import rpc

# this function exposes a service at a given endpoint
def expose_service(subject, name, **configuration):

	# overwrites the default configuration with keys from caller input
	configuration = overwrite(default_service_config, configuration)

	# this is the prefix of the endpoint where the functions on subject will be exposed to distributed access
	configuration['endpoint_prefix'] = name+'/'

	# this function will turn other functions into RPCs
	make_rpc = rpc(**configuration)

	for fn in dir(subject):
		# exposing callable objects to distributed access as RPC
		subject_member = getattr(subject, fn)
		if callable(subject_member):
			make_rpc(subject_member)

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

			child_config = configuration

			# if the member is callable, make it an RPC
			if callable(member):
				# make it an RPC
				make_rpc = rpc(**child_config)
				make_rpc(member)

			# if the member is itself a class, recursively turn it into a ServiceNode
			elif hasattr(member, '__dict__'):
				child_config = overwrite(configuration, {'endpoint_prefix': configuration['endpoint_prefix']+key+'/'})
				child = ServiceNode(member, key, **child_config)
				self.children[key] = child

	def get_profile(self):
		pass