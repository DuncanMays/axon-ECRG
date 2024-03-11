import sys
sys.path.append('..')
import axon
import time
import websockets.sync.server as sync_server
from concurrent.futures import Future
from .serializers import serialize, deserialize
from .transport_client import req_executor, error_handler, AsyncResultHandle

class ITL_Client():

	def __init__(self, socket):
		self.socket = socket

	def call_rpc(self, endpoint, args, kwargs):
		param_str = serialize((args, kwargs))
		req_str = endpoint+' '+param_str
		self.socket.send(req_str)
		result = deserialize(self.socket.recv())
		f = Future()
		f.set_result(error_handler(result))
		return AsyncResultHandle(f)

def sock_serve_fn(websocket):
	profile = deserialize(websocket.recv())

	itl = ITL_Client(websocket)

	stub = axon.client.make_ServiceStub('', itl, profile, stub_type=axon.stubs.SyncStub)

	response = stub.print_str('this is a message from the reflector')

	response = stub.print_str('this is the second message from the reflector')

	response = stub.print_str('this is the third message from the reflector')

	http_tl = axon.transport_worker.HTTPTransportWorker(8081)

	axon.worker.register_ServiceNode(stub, 'reflected_service', tl=http_tl)

	http_tl.run()

	# time.sleep(4)

def run():
	with sync_server.serve(sock_serve_fn, '127.0.0.1', 8080) as server:
		server.serve_forever()