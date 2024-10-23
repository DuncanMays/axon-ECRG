# this file starts a thread with an axon worker in it, for the purposes of testing client code

import threading
import axon
import time
import psutil

# starts a worker thread, fixtures in some tests will add services and RPCs to run tests off this worker instance
# without this check, using the multiprocessing executor will result in this file being run more than once in other processes, and so we must check if we're in the main process before calling init
if (psutil.Process().name() == 'pytest'):

	worker_thread = threading.Thread(target=axon.worker.init, daemon=True, name='axon/tests/__init__.py')
	worker_thread.start()
	time.sleep(1)