import sys
sys.path.append('..')
import axon

import time
from concurrent.futures import ThreadPoolExecutor

e = ThreadPoolExecutor(max_workers=10)

@axon.worker.rpc(executor=e)
def print_this(this):
	print('printing!')
	time.sleep(1)
	print(this)

axon.worker.init()