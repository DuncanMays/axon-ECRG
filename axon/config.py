from sys import argv as cli_args
from importlib import import_module
from types import SimpleNamespace
from axon.inline_executor import InlineExecutor

TL_name = 'axon.HTTP_transport'

if '--tl' in cli_args:
	i = cli_args.index('--tl')
	TL_name = cli_args[i+1]

transport = import_module(TL_name)
inline_executor = InlineExecutor()
version = "0.2.4"
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