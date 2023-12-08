import sys
sys.path.append('..')
import axon

import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# e = ThreadPoolExecutor(max_workers=10)
e = ProcessPoolExecutor(max_workers=10)

# def fn(a):
# 	print('hello')

# def super_fn(a):

# 	result = fn(a)

# 	return result

# e.submit(fn, b'hello').result
# e.submit(super_fn, b'hello').result

# @axon.worker.rpc()
@axon.worker.rpc(executor=e)
def print_this(this):
	print('printing!')
	time.sleep(1)
	print(this)

axon.worker.init()