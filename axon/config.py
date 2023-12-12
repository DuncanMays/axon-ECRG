from types import SimpleNamespace
from .inline_executor import InlineExecutor
inline_executor = InlineExecutor()

version = "0.2.0"
default_service_depth = 3
NUM_OPEN_REQS = 512

default_rpc_config = {
	'comms_pattern': 'simplex',
	'endpoint_prefix': 'rpc/',
	'executor': inline_executor
}

default_service_config = {
	'comms_pattern': 'simplex',
	'endpoint_prefix': '',
	'executor': inline_executor
}

comms_config = {
	'notice_board_port': 8002,
	'request_timeout': 30,
	'worker_port': 8000
}

comms_config = SimpleNamespace(**comms_config)