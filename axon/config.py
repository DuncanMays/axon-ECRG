from types import SimpleNamespace

default_rpc_config = {
	'comms_pattern': 'simplex',
	'endpoint_prefix': 'rpc/',
	'executor': 'Thread',
	'log_errors': False,
	'new_process': False
}

comms_config = {
	'notice_board_port': 8002,
	'request_timeout': 30,
	'RVL_port': 8001,
	'worker_port': 8000
}

comms_config = SimpleNamespace(**comms_config)