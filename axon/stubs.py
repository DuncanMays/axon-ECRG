from .config import comms_config, default_rpc_endpoint

class GenericStub():

	def __init__(self, tl, url):
		self.url = url
		self.tl = tl

	def __call__(self, *args, **kwargs):
		return self.tl.call_rpc(self.url, args, kwargs)

class SyncStub(GenericStub):

	def __init__(self, tl, url):
		GenericStub.__init__(self, tl, url)

	def __call__(self, *args, **kwargs):
		return GenericStub.__call__(self, *args, **kwargs).join()