from sys import path
path.append('..')
import axon
from ServiceNode_tests import TestClass

import asyncio
import threading
import time

@axon.worker.rpc(comms_pattern='simplex')
def simplex_rpc(prefix, suffix='simplex test failed'):
	time.sleep(1)
	return prefix+suffix

@axon.worker.rpc(comms_pattern='duplex')
def duplex_rpc(prefix, suffix='duplex test failed'):
	time.sleep(1)
	return prefix+suffix

t = TestClass()
s = axon.worker.ServiceNode(t, 'test')

worker_thread = threading.Thread(target=axon.worker.init, name='client_test.worker_thread')
worker_thread.daemon = True

async def test_RemoteWorker():
	print('test_RemoteWorker')

	w = axon.client.RemoteWorker('localhost')

	print(await w.rpcs.simplex_rpc('simplex test ', suffix='passed'))
	
	print('----------------------------------------------------')
	# the service node has a dupplex comms pattern
	print('should be duplex')
	print(axon.worker.RPC_node.children['duplex_rpc'].children['__call__']['comms_pattern'])
	print('should be True')
	print(isinstance(w.rpcs.duplex_rpc, axon.stubs.CoroStub))
	print('should be True')
	print(isinstance(w.rpcs.simplex_rpc, axon.stubs.CoroStub))
	print('should be simplex')
	print(w.rpcs.simplex_rpc.comms_pattern)
	print('should be duplex')
	print(w.rpcs.duplex_rpc.comms_pattern)
	# print('should be duplex')
	# print(w.rpcs.duplex_rpc.__call__.comms_pattern)
	print('should be False')
	print(isinstance(w.rpcs.duplex_rpc.__call__, axon.stubs.CoroStub))
	print('----------------------------------------------------')

	print(await w.rpcs.duplex_rpc('duplex test ', suffix='passed'))


	# we also need to test that the service at /test works right

async def main():
	worker_thread.start()

	# waits for the worker's flask app to start
	await asyncio.sleep(0.5)

	await test_RemoteWorker()

asyncio.run(main())