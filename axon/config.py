from types import SimpleNamespace
from .inline_executor import InlineExecutor

from .transport_worker import HTTPTransportWorker
from .transport_client import HTTPTransportClient
from .socket_worker import SocketTransportWorker
from .socket_client import SocketTransportClient

inline_executor = InlineExecutor()

version = "0.2.1"
default_service_depth = 3
default_rpc_endpoint = 'rpc'
NUM_OPEN_REQS = 512
default_client_tl = HTTPTransportClient()
url_scheme = 'http'
# default_client_tl = SocketTransportClient()
# url_scheme = 'ws'

comms_config = {
	'notice_board_port': 8002,
	'request_timeout': 30,
	'worker_port': 8000
}

comms_config = SimpleNamespace(**comms_config)

default_service_config = {
	'endpoint_prefix': '',
	'executor': inline_executor,
	'tl': HTTPTransportWorker(comms_config.worker_port)
	# 'tl': SocketTransportWorker(comms_config.worker_port)
}