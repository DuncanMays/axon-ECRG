# the bit that exports worker profile class and uses the RVL
# an RPC stub is the thing on the client that makes a calling request and waits for the response

from .config import comms_config, default_service_config, default_rpc_config
from .utils import deserialize, GET
from .generic_stubs import GenericStub, SyncStub

from types import SimpleNamespace

def get_ServiceStub(ip_addr='localhost', endpoint_prefix=default_service_config['endpoint_prefix'], name='', profile=None, stub_type=GenericStub, top_stub_type=object):
	global count 

	# the attributes of the returned object
	attrs = {}

	# gets the profile if none are provided
	if (profile == None):
		url = 'http://'+str(ip_addr)+':'+str(comms_config.worker_port)+'/'+endpoint_prefix+name
		print(url)
		_, profile_str = GET(url)
		profile = deserialize(profile_str)

	# once the profil is obtained, metaclass creation is left to get_ServiceStub_helper
	return get_ServiceStub_helper(ip_addr, profile, stub_type, top_stub_type)

def get_ServiceStub_helper(ip_addr, profile, stub_type, top_stub_type):

	attrs = {}
	keys = list(profile.keys())
	banned_keys = ['__call__', '__profile_flag__', '__func__', '__self__', '__get__', '__set__', '__delete__'] + dir(object())

	for key in keys:

		if (key in banned_keys): continue

		member = profile[key]

		if '__profile_flag__' in member:
			# member is a profile for a ServiceNode
			attrs[key] = get_ServiceStub_helper(ip_addr, member, stub_type, object)

		else:
			# If a member is not a profile, then it must be an RPC config, and so correspond to a callable object on the worker with no __dict__attribute
			attrs[key] = stub_type(worker_ip=ip_addr, endpoint_prefix=member['endpoint_prefix']+'/', rpc_name=key)

	parent_classes = (top_stub_type, )

	if '__call__' in keys:
		# if the profile has a __call__ attribute, than the corresponding object on the server is callable and has a __dict__ attribute, and so must be represented by an RPC stub bound to the given network coordinates
		BoundStubClass = get_BoundStubClass(stub_type, ip_addr, profile['__call__'])
		# this ensures the stub will inherit from a stub class that's bound to the configuration
		parent_classes = (BoundStubClass, ) + parent_classes

	ServiceStub = type('ServiceStub', parent_classes, attrs)
	return ServiceStub()

def get_BoundStubClass(stub_type, ip_addr, configuration):
	
	# a class for stubs that are bound to a certain RPC
	class BoundStubClass(stub_type):
		def __init__(self):
			# stub_type.__init__(self, worker_ip=ip_addr, endpoint_prefix=configuration['endpoint_prefix']+'/', rpc_name='__call__', comms_pattern=configuration['comms_pattern'])
			stub_type.__init__(self, worker_ip=ip_addr, endpoint_prefix=configuration['endpoint_prefix']+'/', rpc_name='__call__')

	return BoundStubClass

def get_worker_profile(ip_addr):
	url = 'http://'+str(ip_addr)+':'+str(comms_config.worker_port)+'/_get_profile'
	_, profile_str = GET(url)
	return deserialize(profile_str)

class RemoteWorker():

	def __init__(self, profile_or_ip):
		self.ip_addr = None
		self.rpcs = None

		profile = None

		# profile_or_ip is either an ip address or a worker profile, here we test to see which one
		try:
			profile_or_ip['ip_addr']
			# profile_or_ip has a member ip_addr, and so must be a profile
			profile = profile_or_ip

		except(TypeError):
			# profile_or_ip is an ip address
			profile = get_worker_profile(profile_or_ip)

		# sets up all the rpc stubs
		self.setup(profile)

	def setup(self, profile):
		self.ip_addr = profile['ip_addr']
		self.name = profile['name']

		# this will need to be a lookup on a services key to a number of service profiles
		# self.setup_rpc_stubs(profile['rpcs'])
		self.rpcs = get_ServiceStub(self.ip_addr, endpoint_prefix=default_rpc_config['endpoint_prefix']+'/', name=default_rpc_config['endpoint_prefix'], profile=profile['rpcs'])


		for service_name in profile['services'].keys():
			s = get_ServiceStub(self.ip_addr, endpoint_prefix=f'{service_name}/', name=service_name, profile=profile['services'][service_name])
			setattr(self, service_name, s)

	def setup_rpc_stubs(self, rpcs_descs):
		rpcs = {}

		for rpc_desc in rpcs_descs:
			rpcs[name] = GenericStub(worker_ip=self.ip_addr, rpc_name=rpc_desc['name'], comms_pattern=rpc_desc['comms_pattern'])

		self.rpcs = SimpleNamespace(**rpcs)