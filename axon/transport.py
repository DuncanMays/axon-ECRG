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