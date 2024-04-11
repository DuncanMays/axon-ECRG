from urllib.parse import urlparse, urlunparse

from .config import comms_config, default_rpc_endpoint

# sets the port in url if none are specified
def set_port(url, default_port=comms_config.worker_port):
	comps = urlparse(url)

	if (comps.port == None):
		netloc = f'{comps.hostname}:{default_port}'
		url = urlunparse((comps.scheme, netloc, comps.path, '','' ,  ''))

	return url

class GenericStub():

	def __init__(self, tl, url):
		self.url = set_port(url)
		self.tl = tl

	def __call__(self, *args, **kwargs):
		return self.tl.call_rpc(self.url, args, kwargs)

class SyncStub(GenericStub):

	def __init__(self, tl, url):
		GenericStub.__init__(self, tl, url)

	def __call__(self, *args, **kwargs):
		return GenericStub.__call__(self, *args, **kwargs).join()