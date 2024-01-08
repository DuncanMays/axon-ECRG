from types import SimpleNamespace
from .inline_executor import InlineExecutor
inline_executor = InlineExecutor()

version = "0.2.1"
default_service_depth = 3
default_rpc_endpoint = 'rpc/'
NUM_OPEN_REQS = 512

default_service_config = {
	'endpoint_prefix': '',
	'executor': inline_executor,
	'tl': None
}

comms_config = {
	'notice_board_port': 8002,
	'request_timeout': 30,
	'worker_port': 8000
}

comms_config = SimpleNamespace(**comms_config)