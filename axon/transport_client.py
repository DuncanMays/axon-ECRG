import asyncio
import urllib3
import concurrent.futures as futures
import threading
import inspect

from abc import ABC, abstractmethod
from axon.serializers import AbstractSerializer, deserialize

req_executor = futures.ThreadPoolExecutor(max_workers=100)
http = urllib3.PoolManager(maxsize=100)

# this function checks if an error flag has been set and raises the corresponding error if it has
def error_handler(result_str):

	try:
		err_code, result_str = result_str.split('|', 1)

	except(BaseException):
		raise BaseException(f'Invalid string returned: {result_str}')

	if (err_code == '1'):
		# an error occured in worker, raise it
		error = deserialize(result_str)

		print('the following error occured in worker:')
		raise(error)

	else:
		return result_str


class AsyncResultHandle():

	def __init__(self, fn, *args, **kwargs):
		self.fn = fn
		self.args = args
		self.kwargs = kwargs

	def __await__(self):
		loop = asyncio.get_event_loop()
		return loop.run_in_executor(req_executor, self.fn, *self.args, **self.kwargs).__await__()

	def join(self):
		f = req_executor.submit(self.fn, *self.args, **self.kwargs)
		return f.result()

class AbstractTransportClient(AbstractSerializer):

	def __init__(self):
		super().__init__()

	@abstractmethod
	def get_config(self):
		pass

	@abstractmethod
	def net_call(self, url, param_str):
		pass

	def call_rpc(self, url, args, kwargs):
		param_str = self.serialize((args, kwargs))

		result_str = self.net_call(url, param_str)

		result_str = error_handler(result_str)
		return self.deserialize(result_str)