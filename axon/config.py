from types import SimpleNamespace
from axon.inline_executor import InlineExecutor

# import axon.HTTP_transport as transport
import axon.socket_transport as transport

inline_executor = InlineExecutor()

version = "0.2.1"
default_service_depth = 3
default_rpc_endpoint = 'rpc'
NUM_OPEN_REQS = 512

url_scheme = transport.config.scheme
default_client_tl = transport.client()
default_worker_tl = transport.worker()

comms_config = {
	'notice_board_port': 8002,
	'request_timeout': 30,
}

comms_config = SimpleNamespace(**comms_config)

default_service_config = {
	'endpoint_prefix': '',
	'executor': inline_executor,
	'tl': default_worker_tl
}