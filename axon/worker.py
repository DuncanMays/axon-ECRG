from axon.config import default_rpc_endpoint, default_service_config, default_service_depth
from axon.ServiceNode import ServiceNode, transport_layers

from threading import Thread

def _get_profile():

	service_profiles = {}
	dtl = default_service_config['tl']
	for key in registered_ServiceNodes:
		tl = registered_ServiceNodes[key].tl
		if (dtl == tl):
			service_profiles[key] = registered_ServiceNodes[key].get_profile()

	profile = {
		'rpcs': RPC_node.get_profile(),
		'services': service_profiles,
	}

	return profile

registered_ServiceNodes = {}
# top_service_node = ServiceNode({}, default_service_config['endpoint_prefix'])

def register_ServiceNode(subject, name, depth=default_service_depth, **configuration):

	s = ServiceNode(subject, name, depth=depth, **configuration)
	registered_ServiceNodes[name] = s
	# top_service_node.add_child(name, s, **configuration)
	return s

# a ServiceNode that holds all RPCs associated by this worker instance
RPC_node = ServiceNode(object(), default_rpc_endpoint)

# the RPC decorator adds the associated function to the RPC_node ServiceNode
def rpc(**configuration):
	def add_to_RPC_node(fn):
		RPC_node.add_child(fn.__name__, fn, **configuration)
		return fn

	return add_to_RPC_node

def init(tl=default_service_config['tl']):

	profile_endpoint = f"{default_service_config['endpoint_prefix']}/_get_profile"
	tl.register_RPC(_get_profile, profile_endpoint, default_service_config['executor'])
	transport_layers.add(tl)

	for i in range(len(transport_layers)-1):
		t = transport_layers.pop()
		tl_thread = Thread(target=t.run, daemon=True)
		tl_thread.start()

	last_tl = transport_layers.pop()
	last_tl.run()