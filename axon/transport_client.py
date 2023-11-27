import asyncio
import urllib3
import concurrent.futures as futures
import threading
import inspect

from .utils import serialize, deserialize

req_executor = futures.ThreadPoolExecutor(max_workers=100)
http = urllib3.PoolManager()

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

class AsyncResultHandle():

	def __init__(self, future):
		self.future = future
		self.value = None
		self.depleted = False

	def __await__(self):
		yield
		return self.join()

	def join(self):

		if not self.depleted:
			self.value = self.future.result()
		
		self.depleted = True
		return self.value

def POST_thread_fn(url, data):
	return http.request('POST', url, fields=data)

async def async_POST(url, data=None, timeout=None):
	future = req_executor.submit(POST_thread_fn, url, data)
	x = await AsyncResultHandle(future)
	return x.status, x.data.decode()

def POST(url, data=None, timeout=None):
	future = req_executor.submit(POST_thread_fn, url, data)
	x = future.result()
	return x.status, x.data.decode()

def GET_thread_fn(url):
	return http.request('GET', url)

async def async_GET(url, timeout=None):
	future = req_executor.submit(GET_thread_fn, url)
	x = await AsyncResultHandle(future)
	return x.status, x.data.decode()

def GET(url, timeout=None):
	future = req_executor.submit(GET_thread_fn, url)
	x = future.result()
	return x.status, x.data.decode()

def call_rpc_helper(url, data):
	resp = http.request('POST', url, fields=data)
	return_obj = deserialize(resp.data.decode())
	return error_handler(return_obj)

def call_rpc(url, args, kwargs):
	future = req_executor.submit(call_rpc_helper, url, {'msg': serialize((args, kwargs))})
	return AsyncResultHandle(future)

