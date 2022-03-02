# the bit that exports worker profile class and uses the RVL
# an RPC stub is the thing on the client that makes a calling request and waits for the response

from .config import comms_config
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