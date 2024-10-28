import threading
import time
import sys
sys.path.append('..')

from axon.SocketIO_transport.worker import SocketIOTransportWorker as worker
import axon.inline_executor as ie

w = worker()

def print_x(x):
	print('================================')
	print(x)
	print('================================')
	return x

w.register_RPC(print_x, '/print_x', ie.InlineExecutor())

def big_input(x):
	print('++++++++++++++++++++++++++++++++')
	print(len(str(x)))
	print('++++++++++++++++++++++++++++++++')
	return len(str(x))

w.register_RPC(big_input, '/big_input', ie.InlineExecutor())

worker_thread = threading.Thread(target=w.run, daemon=True, name='axon/tests/SockerIO_transport/__init__.py')
worker_thread.start()
time.sleep(1)