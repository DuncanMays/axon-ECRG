from axon.config import default_rpc_endpoint, default_service_config, default_service_depth
from axon.ServiceNode import ServiceNode, transport_layers
from axon.utils import overwrite

from threading import Thread

registered_ServiceNodes = {}
TLSNs = {}

def get_TLSN(configuration):
	global TLSNs
	configuration = overwrite(default_service_config, configuration)

	top_service_node = None
	tl_id = id(configuration['tl'])

	# record each transport layer we see, and create a top-level ServiceNode for each of them
	# if default_service_config['endpoint_prefix'] in configuration['tl'].rpcs:
	if tl_id in TLSNs:
		top_service_node = TLSNs[tl_id]

	else:
		top_service_node = ServiceNode(object(), '', **configuration)
		top_service_node.add_child(default_rpc_endpoint, object())
		TLSNs[tl_id] = top_service_node

	return top_service_node

def register_ServiceNode(subject, name, depth=default_service_depth, **configuration):
	global TLSNs

	s = ServiceNode(subject, name, depth=depth, **configuration)
	registered_ServiceNodes[name] = s

	top_service_node = get_TLSN(configuration)
	top_service_node.add_child(name, subject, **configuration)

	return s

# # a ServiceNode that holds all RPCs associated by this worker instance
# top_service_node.add_child(default_rpc_endpoint, object(), **default_service_config)
# RPC_node = top_service_node.children[default_rpc_endpoint]

# the RPC decorator adds the associated function to the RPC_node ServiceNode
def rpc(**configuration):
	global TLSNs

	top_service_node = get_TLSN(configuration)
	RPC_node = top_service_node.children[default_rpc_endpoint]

	def add_to_RPC_node(fn):
		RPC_node.add_child(fn.__name__, fn, **configuration)
		return fn

	return add_to_RPC_node

def init(tl=default_service_config['tl']):

	transport_layers.add(tl)

	for i in range(len(transport_layers)-1):
		t = transport_layers.pop()
		tl_thread = Thread(target=t.run, daemon=True)
		tl_thread.start()

	last_tl = transport_layers.pop()
	last_tl.run()