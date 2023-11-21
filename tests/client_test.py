from sys import path
from axon import axon

import pytest
import asyncio
import time

@pytest.mark.asyncio
async def test_RemoteWorker():
	print('test_RemoteWorker')

	w = axon.client.RemoteWorker('localhost')

	print(await w.rpcs.simplex_rpc('simplex test ', suffix='passed'))

	print(w.rpcs)

	# tests that the ServiceStub is set up right
	stub = w.simplex_service

	# tests that child stubs are instantiated properly and that their RPCs work
	for i in range(axon.config.default_service_depth, 0, -1):
		await w.simplex_service()
		w.simplex_service().join()

		await w.simplex_service.test_fn()
		w.simplex_service.test_fn().join()

		if isinstance(w.simplex_service, axon.stubs.GenericStub):
			print('Callable Stub inheritance from axon.stubs.GenericStub confirmed')
		else:
			raise BaseException('Callable Stub stub is not inheritance from axon.stubs.GenericStub')

		if isinstance(w.simplex_service.test_fn, axon.stubs.GenericStub):
			print('RPC inheritance from axon.stubs.GenericStub confirmed')
		else:
			raise BaseException('RPC stub is not inheritance from axon.stubs.GenericStub')

		if (i != 1):
			# if this is the last iteration, worker won't have a child and this line will raise an attribute error
			w.simplex_service = w.simplex_service.child