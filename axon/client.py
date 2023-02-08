# the bit that exports worker profile class and uses the RVL
# an RPC stub is the thing on the client that makes a calling request and waits for the response

from .config import comms_config, default_service_config
from .utils import deserialize, GET
from .simplex_stubs import AsyncSimplexStub, CoroSimplexStub, SyncSimplexStub
from .duplex_stubs import AsyncDuplexStub, CoroDuplexStub, SyncDuplexStub

from types import SimpleNamespace

def get_worker_profile(ip_addr):
	url = 'http://'+str(ip_addr)+':'+str(comms_config.worker_port)+'/_get_profile'
	_, profile_str = GET(url)
	return deserialize(profile_str)

def setup_services(worker, services):
	pass

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

		# sets up all the rfc stubs
		self.setup(profile)

	def setup(self, profile):
		self.ip_addr = profile['ip_addr']
		self.name = profile['name']

		self.setup_rpc_stubs(profile['rpcs'])

	def setup_rpc_stubs(self, rpcs_descs):
		rpcs = {}

		for rpc_desc in rpcs_descs:
			
			comms_pattern = rpc_desc['comms_pattern']
			name = rpc_desc['name']

			if (comms_pattern == 'simplex'):
				rpcs[name] = CoroSimplexStub(worker_ip=self.ip_addr, rpc_name=name)

			elif (comms_pattern == 'duplex'):
				rpcs[name] = CoroDuplexStub(worker_ip=self.ip_addr, rpc_name=name)

			else:
				raise BaseException('unrecognised communication pattern:'+str(comms_pattern))

		self.rpcs = SimpleNamespace(**rpcs)

class ServiceStub():

	def __init__(self, ip_addr='localhost', endpoint_prefix=default_service_config['endpoint_prefix'], name='', profile=None):
		
		self.profile = None
		self.ip_addr = ip_addr
		self.endpoint_prefix = endpoint_prefix
		self.name = name

		if (profile == None):
			url = 'http://'+str(self.ip_addr)+':'+str(comms_config.worker_port)+'/'+self.endpoint_prefix+self.name
			_, profile_str = GET(url)
			profile = deserialize(profile_str)

		self.set_profile(profile)

	def set_profile(self, profile):

		self.profile = profile

		for key in self.profile.keys():

			# __profile_flag__ always maps to True and exists to distinguish between profiles and RPC configurations
			# __class__ maps to a type, which we don't need here and comes with a whole can of worms tied in knots I don't understand
			if (key == '__profile_flag__' or key=='__class__'): continue

			# the serialized representation of a remote object
			member = self.profile[key]
			# will be set to an object that accesses the remote object represented by member
			attribute = None

			if '__profile_flag__' in member:
				# member is a profile for a ServiceNode
				if member['__profile_flag__']:
					# this should always execute since __profile_flag_always maps to True
					if '__call__' in member:
						# if the remote object represented by profile is callable, it will have a __call__ key. It might have useful attributes if it's callable, so we can't represent it with an attribute-less RPC stub. What we'll do instead is make the stub's __call__ attribute an RPC stub
						attribute = CallableServiceStub(member['__call__'], ip_addr=self.ip_addr, endpoint_prefix=self.endpoint_prefix+'/'+key, name=self.name, profile=member)

					else:
						attribute = ServiceStub(ip_addr=self.ip_addr, endpoint_prefix=self.endpoint_prefix+'/'+key, name=self.name, profile=member)

				else:
					# this means something is very wrong
					raise(BaseException('service profile with __profile_flag__ set to False'))

			else:

				# member is a configuration dict for an RPC
				comms_pattern = member['comms_pattern']

				if (comms_pattern == 'simplex'):
					attribute = CoroSimplexStub(worker_ip=self.ip_addr, endpoint_prefix=self.endpoint_prefix+'/', rpc_name=key)

				elif (comms_pattern == 'duplex'):
					attribute = CoroDuplexStub(worker_ip=self.ip_addr, endpoint_prefix=self.endpoint_prefix+'/', rpc_name=key)

				else:
					raise BaseException('unrecognised communication pattern:'+str(comms_pattern))


			setattr(self, key, attribute)
	

class CallableServiceStub(ServiceStub):

	def __init__(self, self_config, *args, **kwargs):
		ServiceStub.__init__(self, *args, **kwargs)

		# self_config is a configuration dict for an RPC
		comms_pattern = self_config['comms_pattern']

		if (comms_pattern == 'simplex'):
			self.___call___ = CoroSimplexStub(worker_ip=self.ip_addr, endpoint_prefix=self.endpoint_prefix+'/', rpc_name='__call__')

		elif (comms_pattern == 'duplex'):
			self.___call___ = CoroDuplexStub(worker_ip=self.ip_addr, endpoint_prefix=self.endpoint_prefix+'/', rpc_name='__call__')

		else:
			raise BaseException('unrecognised communication pattern:'+str(comms_pattern)) 

	async def __call__(self, *args, **kwargs):
		return await self.___call___(*args, **kwargs)

def get_MetaStub( ip_addr='localhost', endpoint_prefix=default_service_config['endpoint_prefix'], name='', profile=None, parent_class=object):
	global count 

	# the attributes of the returned object
	attrs = {}

	# gets the profile if none are provided
	if (profile == None):
		url = 'http://'+str(ip_addr)+':'+str(comms_config.worker_port)+'/'+endpoint_prefix+name
		_, profile_str = GET(url)
		profile = deserialize(profile_str)
		# print(profile)

	# once the profil is obtained, metaclass creation is left to get_MetaStub_helper
	return get_MetaStub_helper(ip_addr, profile, parent_class)

def get_MetaStub_helper(ip_addr, profile, parent_class):

	keys = list(profile.keys())
	parent_classes = (parent_class, )
	attrs = {}

	banned_keys = ['__profile_flag__', '__func__', '__self__', '__get__', '__set__', '__delete__'] + dir(object())

	if '__call__' in keys:
		# if the profile has a __call__ attribute, than the corresponding object on the server is callable, and so must be represented by an RPC stub, bound to the given network coordinates
		BoundStubClass = get_BoundStubClass(ip_addr, profile['__call__'])
		# this ensures the stub will inherit from a stub class that's bound to the configuration
		parent_classes = (BoundStubClass, ) + parent_classes

	for key in keys:

		if (key in banned_keys): continue

		member = profile[key]

		if '__profile_flag__' in member:
			# member is a profile for a ServiceNode

			if not member['__profile_flag__']:
				# this block of code should never execute
				raise(BaseException('service profile with __profile_flag__ set to False'))

			# if '__call__' in member:
			# 	# if the profile has a __call__ attribute, than the corresponding object on the server is callable, and so must be represented by an RPC stub, bound to the given network coordinates
			# 	BoundStubClass = get_BoundStubClass(ip_addr, member['__call__'])
			# 	attrs[key] = get_MetaStub_helper(ip_addr, member, BoundStubClass)

			else:
				# else the stub simply inherits from object
				attrs[key] = get_MetaStub_helper(ip_addr, member, object)

	MetaStub = type('MetaStub', parent_classes, attrs)
	return MetaStub()

def get_BoundStubClass(ip_addr, configuration):
	comms_pattern = configuration['comms_pattern']
	baseClass = None

	if (comms_pattern == 'simplex'):
		baseClass = CoroSimplexStub

	elif (comms_pattern == 'duplex'):
		baseClass = CoroDuplexStub

	else:
		raise BaseException(f'unrecognised comms_pattern: {comms_pattern}')
	
	# a class for stubs that are bound to a certain RPC
	class BoundStubClass(baseClass):
		def __init__(self):
			baseClass.__init__(self, worker_ip=ip_addr, endpoint_prefix=configuration['endpoint_prefix']+'/', rpc_name='__call__')

	return BoundStubClass

def get_RPC_stub(ip_addr, configuration):
	comms_pattern = configuration['comms_pattern']
	stub = None

	if (comms_pattern == 'simplex'):
		stub = CoroSimplexStub(worker_ip=ip_addr, endpoint_prefix=configuration['endpoint_prefix']+'/', rpc_name='__call__')

	elif (comms_pattern == 'duplex'):
		stub = CoroDuplexStub(worker_ip=ip_addr, endpoint_prefix=configuration['endpoint_prefix']+'/', rpc_name='__call__')
	
	return stub

def get_RPC_stub_2(ip_addr, configuration):
	def return_fn(*args):
		return 'this is a test RPC stub'

	return return_fn