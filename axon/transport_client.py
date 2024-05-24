import asyncio
import urllib3
import concurrent.futures as futures
import threading
import inspect

from abc import ABC, abstractmethod

from axon.serializers import serialize, deserialize

req_executor = futures.ThreadPoolExecutor(max_workers=100)
http = urllib3.PoolManager()

# this function checks if an error flag has been set and raises the corresponding error if it has
def error_handler(result_str):
	err_code, result_str = result_str.split('|', 1)

	if (err_code == '1'):
		# an error occured in worker, raise it
		(error_info, error) = deserialize(result_str)

		print('the following error occured in worker:')
		print(error_info)
		raise(error)

	else:
		return result_str

# class AsyncResultHandle():

# 	def __init__(self, future):
# 		self.future = future
# 		self.value = None
# 		self.depleted = False

# 	def __await__(self):
# 		yield
# 		return self.join()

# 	def join(self):

# 		if not self.depleted:
# 			self.value = self.future.result()
		
# 		self.depleted = True
# 		return self.value

class AsyncResultHandle():

	def __init__(self, fn, *args, **kwargs):
		self.fn = fn
		self.args = args
		self.kwargs = kwargs

	def __await__(self):
		# yield
		loop = asyncio.get_event_loop()
		print(id(loop))
		print(loop.is_closed())
		t = loop.run_in_executor(req_executor, self.fn, *self.args, **self.kwargs).__await__()
		print(loop.is_closed())
		return t

	def join(self):

		# if not self.depleted:
		# 	self.value = self.future.result()
		
		f = req_executor.submit(self.fn, *self.args, **self.kwargs)
		return f.result()

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

class AbstractTransportClient(ABC):

	@abstractmethod
	def get_config(self):
		pass

	@abstractmethod
	def call_rpc(self, url, args, kwargs):
		pass