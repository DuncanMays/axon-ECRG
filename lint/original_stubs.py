from .utils import serialize, deserialize, GET, POST, async_GET, async_POST
from .config import comms_config, default_rpc_config
from .return_value_linker import ReturnEvent_coro, RVL

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

def error_handler(worker_ip, return_obj):
	if (return_obj['errcode'] == 1):
		# an error occured in worker, raise it
		(error_info, error) = return_obj['result']

		print('the following error occured in worker at '+str(worker_ip)+':')
		print(error_info)
		raise(error)

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

		if (text =='duplex'):
			raise(BaseException('simplex call sent to duplex RPC'))

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
		return_event = ReturnEvent_coro()
		rvl.register(call_id, return_event)

		# this object holds information about the function call that the worker will need to provide to the rvl upon completion
		call_info = {'id': call_id, 'rvl_port': rvl.port}

		# makes the calling request
		status, text = await async_POST(url=url , data={'msg': serialize((call_info, args, kwargs))})
		return_obj = deserialize(text)

		# raises exception if the receiving RPC is simplex, not duplex
		if (return_obj != 'duplex'):
			print(return_obj)
			raise(BaseException('duplex call sent to simplex RPC'))

		# we now wait for the result to return
		return_obj = await return_event.get_return_value()

		# detects if an error was thrown in worker
		return error_handler(worker_ip, return_obj)

	return duplex_rpc_stub
