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
			if (key == '__profile_flag__' or key=='__class__'): continue

			# the serialized representation of a remote object
			member = self.profile[key]
			# will be set to an object that accesses the remote object represented by member
			attribute = None

			if '__profile_flag__' in member:
				# member is a profile for a ServiceNode
				if member['__profile_flag__']:
					if '__call__' in member:
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
		