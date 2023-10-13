from sys import path
path.append('..')
import axon
from ServiceNode_tests import TestClass

import asyncio
import threading
import time

default_service_depth = axon.config.default_service_depth

@axon.worker.rpc(comms_pattern='simplex')
def simplex_rpc(prefix, suffix='simplex test failed'):
	time.sleep(1)
	return prefix+suffix

@axon.worker.rpc(comms_pattern='duplex')
def duplex_rpc(prefix, suffix='duplex test failed'):
	time.sleep(1)
	return prefix+suffix

t = TestClass()
s = axon.worker.register_ServiceNode(t, 'test')

worker_thread = threading.Thread(target=axon.worker.init, name='client_test.worker_thread')
worker_thread.daemon = True

async def test_RemoteWorker():
	print('test_RemoteWorker')

	w = axon.client.RemoteWorker('localhost')

	print(await w.rpcs.simplex_rpc('simplex test ', suffix='passed'))
	print(await w.rpcs.duplex_rpc('duplex test ', suffix='passed'))

	# tests that the ServiceStub is set up right
	stub = w.test

	# tests that child stubs are instantiated properly and that their RPCs work
	for i in range(default_service_depth, 0, -1):
		await w.test.test_fn()

		if isinstance(w.test.test_fn, axon.stubs.GenericStub):
			print('RPC inheritance from axon.stubs.GenericStub confirmed')
		else:
			raise BaseException('RPC stub is not inheritance from axon.stubs.GenericStub')

		# idk how to tell if w.test is a ServiceStub

		if (i != 1):
			# if this is the last iteration, worker won't have a child and this line will raise an attribute error
			w.test = w.test.child

async def main():
	worker_thread.start()

	# waits for the worker's flask app to start
	await asyncio.sleep(0.5)

	await test_RemoteWorker()

asyncio.run(main())