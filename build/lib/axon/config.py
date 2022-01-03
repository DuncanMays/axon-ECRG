from types import SimpleNamespace

default_rpc_config = {
	'comms_pattern': 'simplex',
	'new_process': False
}

comms_config = {
	'notice_board_ip': '192.168.229.12',
	'notice_board_port': 8002,
	'request_timeout': 30,
	'RVL_port': 8001,
	'worker_port': 8000
}

comms_config = SimpleNamespace(**comms_config)