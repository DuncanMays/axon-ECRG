import threading
import time
import sys
sys.path.append('..')

import axon.SocketIO_transport.worker as worker
import axon.inline_executor as ie

w = worker.SocketIOTransportWorker()

def fn(x):
	print('================================')
	print(x)
	print('================================')
	return x

w.register_RPC(fn, '/endpoint', ie.InlineExecutor())

worker_thread = threading.Thread(target=w.run, daemon=True, name='axon/tests/SockerIO_transport/__init__.py')
worker_thread.start()
time.sleep(1)