from sys import path
path.append('./')
path.append('./unit_tests')
import axon
import pytest
import asyncio
import time

default_service_depth = axon.config.default_service_depth

async def check_properties():
	print('test_RemoteWorker')

	w = axon.client.RemoteWorker('localhost')

	print(await w.rpcs.simplex_rpc('simplex test ', suffix='passed'))
	print(await w.rpcs.duplex_rpc('duplex test ', suffix='passed'))

	# tests that the ServiceStub is set up right
	stub = w.simplex_service

	# tests that child stubs are instantiated properly and that their RPCs work
	for i in range(default_service_depth, 0, -1):
		await w.simplex_service.test_fn()

		if isinstance(w.simplex_service.test_fn, axon.stubs.GenericStub):
			print('RPC inheritance from axon.stubs.GenericStub confirmed')
		else:
			raise BaseException('RPC stub is not inheritance from axon.stubs.GenericStub')

		# idk how to tell if w.test is a ServiceStub

		if (i != 1):
			# if this is the last iteration, worker won't have a child and this line will raise an attribute error
			w.simplex_service = w.simplex_service.child

@pytest.mark.asyncio
async def test_RemoteWorker():
	# worker_thread.start()

	# waits for the worker's flask app to start
	await asyncio.sleep(0.5)

	await check_properties()