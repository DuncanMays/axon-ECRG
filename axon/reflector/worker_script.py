import sys
sys.path.append('..')

import axon
from concurrent.futures import ThreadPoolExecutor

itlw = axon.reflector.ITLW(url='143.198.32.69', name='test_worker')
tpe = ThreadPoolExecutor(max_workers=10)

@axon.worker.rpc(tl=itlw)
def echo(msg):
	raise BaseException('this is an error!')
	return msg

axon.worker.init()