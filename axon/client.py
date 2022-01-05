# the bit that exports worker profile class and uses the RVL
# an RPC stub is the thing on the client that makes a calling request and waits for the response

from .utils import serialize, deserialize, GET, POST, async_GET, async_POST
from .config import comms_config, default_rpc_config
from .return_value_linker import ReturnEvent, RVL

from types import SimpleNamespace
import asyncio
import types
import uuid

rvl = None

async def start_client():
	global rvl

	loop = asyncio.get_running_loop()
	rvl = RVL(loop)
	rvl.start()

def get_worker_profile(ip_addr):
	url = 'http://'+str(ip_addr)+':'+str(comms_config.worker_port)+'/_get_profile'
	_, profile_str = GET(url)
	return deserialize(profile_str)

def error_handler(worker_ip, return_obj):
	if (return_obj['errcode'] == 1):
		# an error occured in worker, raise it
		(error_class, error_instance) = return_obj['result']

		print('an error occured in worker at '+str(worker_ip)+':')
		raise(error_instance)

	else:
		# returns the result
		return return_obj['result']

def get_simplex_rpc_stub(worker_ip, rpc_name):

	# URL of RPC
	url = 'http://'+str(worker_ip)+':'+str(comms_config.worker_port)+'/'+default_rpc_config['endpoint_prefix']+rpc_name

	# this function makes a calling request to a simplex RPC on the worker with IP worker_ip to the RPC named rpc_name
	async def simplex_rpc_stub(*args, **kwargs):
		
		# makes the calling request
		status, text = await async_POST(url=url , data={'msg': serialize((args, kwargs))})
		# deserializes return object from worker
		return_obj = deserialize(text)
		return error_handler(worker_ip, return_obj)

	return simplex_rpc_stub

def get_multicast_simplex_rpc_stub(worker_ips, rpc_name):

	# URLs of RPCs
	get_url = lambda ip : 'http://'+str(ip)+':'+str(comms_config.worker_port)+'/'+default_rpc_config['endpoint_prefix']+rpc_name
	urls = [get_url(ip) for ip in worker_ips]

	# this function makes a calling request to a simplex RPC on the worker with IP worker_ip to the RPC named rpc_name
	async def multicast_simplex_rpc_stub(arg_list, kwargs_list, shared_args, shared_kwargs):
		
		# makes the calling requests

		status, text = await async_POST(url=url , data={'msg': serialize((args, kwargs))})
		# deserializes return object from worker
		return_obj = deserialize(text)
		return error_handler(worker_ip, return_obj)

	return simplex_rpc_stub

def get_duplex_rpc_stub(worker_ip, rpc_name):

	# the URL of the RPC
	url = 'http://'+str(worker_ip)+':'+str(comms_config.worker_port)+'/'+default_rpc_config['endpoint_prefix']+rpc_name

	# this function makes a calling request to a simplex RPC on the worker with IP worker_ip to the RPC named rpc_name
	async def duplex_rpc_stub(*args, **kwargs):
		global rvl
		if rvl == None:
			await start_client()

		# we must register an event listenner with the return value linker, which will wait for the incomming result request
		# this uuid will identify the call, so the RVL can lookup the event
		call_id = uuid.uuid4()
		return_event = ReturnEvent()
		rvl.register(call_id, return_event)

		# this object holds information about the function call that the worker will need to provide to the rvl upon completion
		call_info = {'id': call_id, 'rvl_port': rvl.port}

		# makes the calling request
		status, text = await async_POST(url=url , data={'msg': serialize((call_info, args, kwargs))})
		return_obj = deserialize(text)

		# raises exception if the receiving RPC is simplex, not duplex
		if (return_obj == 'simplex'):
			print(return_obj)
			raise(BaseException('duplex call sent to simplex RPC'))

		# we now wait for the result to return
		return_obj = await return_event.get_return_value()

		# detects if an error was thrown in worker
		return error_handler(worker_ip, return_obj)

	return duplex_rpc_stub

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

	def setup_rpc_stubs(self, rpcs_profiles):
		rpcs = {}

		for rpc_desc in rpcs_profiles:
			
			name = rpc_desc['name']
			configuration = rpc_desc['configuration']

			if (configuration['comms_pattern'] == 'simplex'):
				rpcs[name] = get_simplex_rpc_stub(self.ip_addr, name)

			elif (configuration['comms_pattern'] == 'duplex'):
				rpcs[name] = get_duplex_rpc_stub(self.ip_addr, name)
			else:
				raise BaseException('unrecognised communication pattern:'+str(configuration['comms_pattern']))

		self.rpcs = SimpleNamespace(**rpcs)