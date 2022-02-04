import sys
sys.path.append('..')

from axon import worker
import time, random

@worker.rpc()
def wait(a):
	time.sleep(random.randint(0, 3))
	print(a)

worker.init()