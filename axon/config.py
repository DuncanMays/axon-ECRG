from types import SimpleNamespace

version = "0.1.5"
default_service_depth = 1

default_rpc_config = {
	'comms_pattern': 'simplex',
	'endpoint_prefix': 'rpc/',
	'executor': 'inline'
}

default_service_config = {
	'comms_pattern': 'simplex',
	'endpoint_prefix': '',
	'executor': 'inline'
}

comms_config = {
	'notice_board_port': 8002,
	'request_timeout': 30,
	'RVL_port': 8001,
	'worker_port': 8000
}

comms_config = SimpleNamespace(**comms_config)