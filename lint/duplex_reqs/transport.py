from .utils import serialize, deserialize, GET, POST, async_GET, async_POST
from .config import comms_config, default_rpc_config
from .return_value_linker import ReturnEvent_async, ReturnEvent_coro, RVL

import threading
import asyncio
import uuid

# this function checks if an error flag has been set and raises the corresponding error if it has
def error_handler(return_obj):
	if (return_obj['errcode'] == 1):
		# an error occured in worker, raise it
		(error_info, error) = return_obj['result']

		print('the following error occured in worker:')
		print(error_info)
		raise(error)

	else:
		# returns the result
		return return_obj['result']

# this function makes a calling request to a simplex RPC
async def call_simplex_rpc_coro(url, args, kwargs):
	
	# makes the calling request
	status, text = await async_POST(url=url , data={'msg': serialize((args, kwargs))})

	if (text =='duplex'):
		raise(BaseException('simplex call sent to duplex RPC'))

	# deserializes return object from worker
	return_obj = deserialize(text)
	return error_handler(return_obj)

class AsyncCallHandle():

	def __init__(self, response_event):
		self.response_event = response_event

	def join(self):
		text = self.response_event.get_return_value()

		if (text =='duplex'):
			raise(BaseException('simplex call sent to duplex RPC'))

		# deserializes return object from worker
		return_obj = deserialize(text)
		return error_handler(return_obj)

# this function makes a calling request to a simplex RPC, and returns a handle which will block and return the result of the request on .join
def call_simplex_rpc_async(url, args, kwargs):

	response_event = ReturnEvent_async()
	
	def thread_fn(response_event):
		# makes the calling request
		status, text = POST(url=url , data={'msg': serialize((args, kwargs))})
		response_event.put_return_value(text)

	request_thread = threading.Thread(target=thread_fn, args=(response_event, ), name='call_duplex_rpc_async.request_thread')
	request_thread.start()

	return AsyncCallHandle(response_event)

# this function makes a calling request to a simplex RPC
def call_simplex_rpc_sync(url, args, kwargs):
	status, text = POST(url=url , data={'msg': serialize((args, kwargs))})
	
	if (text =='duplex'):
		raise(BaseException('simplex call sent to duplex RPC'))

	# deserializes return object from worker
	# print(text)
	return_obj = deserialize(text)
	return error_handler(return_obj)

# the Return Value Linker is an app that runs in a separate thread and listens for incomming HTTP requests carrying the results from duplex RPC calls
rvl = RVL()

# this function checks to see if the RVL ap is running, and if not, starts it
def ensure_rvl_app():
	global rvl

	if not rvl.running:
		rvl.start_app()

# this function ensures the RVL is active and listening for the return value and then makes a calling request to a duplex RPC
def call_duplex_rpc_async(url, args, kwargs):

	global rvl

	# checks that the RVL is active, and if not, starts one
	ensure_rvl_app()

	return_event = ReturnEvent_async()

	def thread_fn(return_event):
		# we must register an event listenner with the return value linker, which will wait for the incomming result request
		# this uuid will identify the call, so the RVL can lookup the event
		call_id = uuid.uuid4()
		rvl.register(call_id, return_event)

		# this object holds information about the function call that the worker will need to provide to the rvl upon completion
		call_info = {'id': call_id, 'rvl_port': rvl.port}

		# makes the calling request
		status, text = POST(url=url , data={'msg': serialize((call_info, args, kwargs))})
		return_obj = deserialize(text)

		# raises exception if the receiving RPC is simplex, not duplex
		if (return_obj != 'duplex'):
			print(return_obj)
			raise(BaseException('duplex call sent to simplex RPC'))

	request_thread = threading.Thread(target=thread_fn, args=(return_event, ), name='call_duplex_rpc_async.request_thread')
	request_thread.start()

	return AsyncCallHandle(return_event)

# this function ensures the RVL is active and listening for the return value and then makes a calling request to a duplex RPC
async def call_duplex_rpc_coro(url, args, kwargs):
	global rvl
	
	ensure_rvl_app()

	# we must register an event listenner with the return value linker, which will wait for the incomming result request
	# this uuid will identify the call, so the RVL can lookup the event
	call_id = uuid.uuid4()
	return_event = ReturnEvent_coro()
	await return_event.init()
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
	serialized_result = await return_event.get_return_value()

	# deserializes result
	result = deserialize(serialized_result)

	# detects if an error was thrown in worker
	return error_handler(result)

# this function ensures the RVL is active and listening for the return value and then makes a calling request to a duplex RPC
def call_duplex_rpc_sync(url, args, kwargs):
	global rvl
	
	ensure_rvl_app()

	# we must register an event listenner with the return value linker, which will wait for the incomming result request
	# this uuid will identify the call, so the RVL can lookup the event
	call_id = uuid.uuid4()
	return_event = ReturnEvent_async()
	rvl.register(call_id, return_event)

	# this object holds information about the function call that the worker will need to provide to the rvl upon completion
	call_info = {'id': call_id, 'rvl_port': rvl.port}

	# makes the calling request
	status, text = POST(url=url , data={'msg': serialize((call_info, args, kwargs))})
	return_obj = deserialize(text)

	# raises exception if the receiving RPC is simplex, not duplex
	if (return_obj != 'duplex'):
		print(return_obj)
		raise(BaseException('duplex call sent to simplex RPC'))

	# we now wait for the result to return
	serialized_result = return_event.get_return_value()

	# deserializes result
	result = deserialize(serialized_result)

	# detects if an error was thrown in worker
	return error_handler(result)