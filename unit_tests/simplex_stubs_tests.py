import threading
import asyncio
import time

from sys import path
path.append('..')

import axon

def test_error_wrappers():
	print('test_error_wrappers')

	def test_fn():
		raise(BaseException('this is the exception that is raised if everything works'))

	wrapped_fn = axon.comms_wrappers.error_wrapper(test_fn)

	return_obj = wrapped_fn((), {})

	try:
		axon.simplex_stubs.error_handler(return_obj)
	except(BaseException):
		print('test passed')

# gotta set up a worker to test the stubs on

@axon.worker.rpc()
def simplex_rpc(prefix, suffix=' test failed'):
	return prefix+suffix

worker_thread = threading.Thread(target=axon.worker.init)
worker_thread.daemon = True

async def test_coro_stub():
	print('test_coro_stub')

	rpc_name = 'simplex_rpc'
	url = 'http://localhost:'+str(axon.config.comms_config.worker_port)+'/'+axon.config.default_rpc_config['endpoint_prefix']+rpc_name+'/__call__'
	print(url)

	result = await axon.simplex_stubs.call_simplex_rpc_coro(url, ('test ', ), {'suffix':'passed!', })

	print(result)

def test_async_stub():
	print('test_async_stub')

	rpc_name = 'simplex_rpc'
	url = 'http://localhost:'+str(axon.config.comms_config.worker_port)+'/'+axon.config.default_rpc_config['endpoint_prefix']+rpc_name

	resultHandle = axon.simplex_stubs.call_simplex_rpc_async(url, ('test ', ), {'suffix':'passed!', })

	print(resultHandle.join())

def test_sync_stub():
	print('test_sync_stub')

	rpc_name = 'simplex_rpc'
	url = 'http://localhost:'+str(axon.config.comms_config.worker_port)+'/'+axon.config.default_rpc_config['endpoint_prefix']+rpc_name

	print(axon.simplex_stubs.call_simplex_rpc_sync(url, ('test ', ), {'suffix':'passed!', }))

async def test_GenericSimplexStub():
	print('test_GenericSimplexStub')

	stub = axon.simplex_stubs.GenericSimplexStub(worker_ip='localhost', rpc_name='simplex_rpc')

	call_handle = stub.async_call(('test ', ), {'suffix':'passed!', })
	print(call_handle.join())

	print(await stub.coro_call(('test ', ), {'suffix':'passed!', }))

	print(stub.sync_call(('test ', ), {'suffix':'passed!', }))

async def test_AsyncSimplexStub():
	print('test_AsyncSimplexStub')

	stub = axon.simplex_stubs.AsyncSimplexStub(worker_ip='localhost', rpc_name='simplex_rpc')
	handle = stub('test ', suffix='passed!')
	print(handle.join())

	handle = stub.async_call(('test ', ), {'suffix':'passed!', })
	print(handle.join())
	print(await stub.coro_call(('test ', ), {'suffix':'passed!', }))
	print(stub.sync_call(('test ', ), {'suffix':'passed!', }))

async def test_CoroSimplexStub():
	print('test_CoroSimplexStub')

	stub = axon.simplex_stubs.CoroSimplexStub(worker_ip='localhost', rpc_name='simplex_rpc')
	print(await stub('test ', suffix='passed!'))

	handle = stub.async_call(('test ', ), {'suffix':'passed!', })
	print(handle.join())
	print(await stub.coro_call(('test ', ), {'suffix':'passed!', }))
	print(stub.sync_call(('test ', ), {'suffix':'passed!', }))

async def test_SyncSimplexStub():
	print('test_SyncSimplexStub')

	stub = axon.simplex_stubs.SyncSimplexStub(worker_ip='localhost', rpc_name='simplex_rpc')
	print(stub('test ', suffix='passed!'))

	handle = stub.async_call(('test ', ), {'suffix':'passed!', })
	print(handle.join())
	print(await stub.coro_call(('test ', ), {'suffix':'passed!', }))
	print(stub.sync_call(('test ', ), {'suffix':'passed!', }))

async def main():
	test_error_wrappers()

	print('starting worker thread for testing stubs against')
	worker_thread.start()

	time.sleep(1)

	await test_coro_stub()

	# test_async_stub()

	# test_sync_stub()

	# await test_GenericSimplexStub()

	# await test_AsyncSimplexStub()
	# await test_CoroSimplexStub()
	# await test_SyncSimplexStub()

if (__name__ == '__main__'): asyncio.run(main())