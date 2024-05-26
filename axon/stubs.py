from axon.transport_client import AsyncResultHandle, req_executor

from urllib.parse import urlparse, urlunparse
import asyncio

def add_url_defaults(url, config):
	
	if '://' not in url:
		url = config.scheme+'://'+url

	comps = urlparse(url)

	if (comps.port == None):
		netloc = f'{comps.hostname}:{config.port}'
		url = urlunparse((comps.scheme, netloc, comps.path, '', '' , ''))

	return url

class GenericStub():

	def __init__(self, tl, url):
		self.url = add_url_defaults(url, tl.get_config())
		self.tl = tl

	def __call__(self, *args, **kwargs):
		return AsyncResultHandle(self.tl.call_rpc, self.url, args, kwargs)

class FutureStub(GenericStub):

	def __init__(self, tl, url):
		GenericStub.__init__(self, tl, url)

	def __call__(self, *args, **kwargs):
		return req_executor.submit(self.tl.call_rpc, self.url, args, kwargs)

class SyncStub(GenericStub):

	def __init__(self, tl, url):
		GenericStub.__init__(self, tl, url)

	def __call__(self, *args, **kwargs):
		return self.tl.call_rpc(self.url, args, kwargs)