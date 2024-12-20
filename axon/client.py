# the bit that exports worker profile class and uses the RVL
# an RPC stub is the thing on the client that makes a calling request and waits for the response

from axon.config import default_service_config, default_rpc_endpoint, default_client_tl
from axon.stubs import GenericStub, add_url_defaults

from types import SimpleNamespace

transport_client = default_client_tl

def get_stub(url, tl=transport_client, stub_type=GenericStub, top_stub_type=object):
	url = add_url_defaults(url, tl.get_config())
	profile = tl.call_rpc(url, (), {})
	url_components = url.split('/')
	base_url = '/'.join(url_components[:3])
	return make_ServiceStub(base_url, tl, profile, stub_type, top_stub_type)

def make_ServiceStub(url, tl, profile, stub_type=GenericStub, top_stub_type=object):

	attrs = {}
	keys = list(profile.keys())
	parent_classes = (top_stub_type, )
	banned_keys = ['__call__', '__profile_flag__', '__func__', '__self__', '__get__', '__set__', '__delete__'] + dir(object())

	for key in keys:

		if (key in banned_keys): continue

		member = profile[key]

		if '__profile_flag__' in member:
			# member is a profile for a ServiceNode
			attrs[key] = make_ServiceStub(url, tl, member, stub_type, object)

		else:
			# If a member is not a profile, then it must be an RPC config, and so correspond to a callable object on the worker with no __dict__attribute
			stub_url = url + f"{member['endpoint_prefix']}/{key}"
			attrs[key] = stub_type(tl=tl, url=stub_url)

	if '__call__' in keys:
		# if the profile has a __call__ attribute, than the corresponding object on the server is callable and has a __dict__ attribute, and so must be represented by an RPC stub bound to the given network coordinates
		stub_url = url + f"{profile['__call__']['endpoint_prefix']}/__call__"
		BoundStubClass = get_BoundStubClass(stub_type, tl, stub_url)
		# this ensures the stub will inherit from a stub class that's bound to the configuration
		parent_classes = (BoundStubClass, ) + parent_classes

	ServiceStub = type('ServiceStub', parent_classes, attrs)
	return ServiceStub()

def get_BoundStubClass(stub_type, tl, url):
	
	# a class for stubs that are bound to a certain RPC
	class BoundStubClass(stub_type):
		def __init__(self):
			stub_type.__init__(self, tl, url)

	return BoundStubClass