from types import SimpleNamespace
from axon.inline_executor import InlineExecutor

from axon.socket_worker import SocketTransportWorker
from axon.socket_client import SocketTransportClient

import axon.HTTP_transport as transport

inline_executor = InlineExecutor()

version = "0.2.1"
default_service_depth = 3
default_rpc_endpoint = 'rpc'
NUM_OPEN_REQS = 512
default_client_tl = transport.client()
url_scheme = transport.config.scheme

comms_config = {
	'notice_board_port': 8002,
	'request_timeout': 30,
	'worker_port': 8000
}

comms_config = SimpleNamespace(**comms_config)

default_service_config = {
	'endpoint_prefix': '',
	'executor': inline_executor,
	'tl': transport.worker(comms_config.worker_port)
}