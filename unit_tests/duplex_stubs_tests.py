import threading
import asyncio
import time

from sys import path
path.append('..')

import axon

def test_async_stub():
	print('test_async_stub')

	rpc_name = 'duplex_rpc'
	url = 'http://localhost:'+str(axon.config.comms_config.worker_port)+'/'+axon.config.default_rpc_config['endpoint_prefix']+rpc_name+'/__call__'

	resultHandle = axon.duplex_stubs.call_duplex_rpc_async(url, ('test ', ), {'suffix':'passed!', })

	print(resultHandle.join())

async def test_coro_stub():
	print('test_coro_stub')

	rpc_name = 'duplex_rpc'
	url = 'http://localhost:'+str(axon.config.comms_config.worker_port)+'/'+axon.config.default_rpc_config['endpoint_prefix']+rpc_name+'/__call__'

	result = await axon.duplex_stubs.call_duplex_rpc_coro(url, ('test ', ), {'suffix':'passed!', })

	print(result)

def test_sync_stub():
	print('test_sync_stub')

	rpc_name = 'duplex_rpc'
	url = 'http://localhost:'+str(axon.config.comms_config.worker_port)+'/'+axon.config.default_rpc_config['endpoint_prefix']+rpc_name+'/__call__'

	result = axon.duplex_stubs.call_duplex_rpc_sync(url, ('test ', ), {'suffix':'passed!', })

	print(result)


async def test_GenericDuplexStub():
	print('test_GenericDuplexStub')

	stub = axon.duplex_stubs.GenericDuplexStub(worker_ip='localhost', rpc_name='duplex_rpc')

	call_handle = stub.async_call(('test ', ), {'suffix':'passed!', })
	print(call_handle.join())

	print(await stub.coro_call(('test ', ), {'suffix':'passed!', }))

	print(stub.sync_call(('test ', ), {'suffix':'passed!', }))

async def test_AsyncDuplexStub():
	print('test_AsyncDuplexStub')

	stub = axon.duplex_stubs.AsyncDuplexStub(worker_ip='localhost', rpc_name='duplex_rpc')
	handle = stub('test ', suffix='passed!')
	print(handle.join())

	handle = stub.async_call(('test ', ), {'suffix':'passed!', })
	print(handle.join())
	print(await stub.coro_call(('test ', ), {'suffix':'passed!', }))
	print(stub.sync_call(('test ', ), {'suffix':'passed!', }))

async def test_CoroDuplexStub():
	print('test_CoroDuplexStub')

	stub = axon.duplex_stubs.CoroDuplexStub(worker_ip='localhost', rpc_name='duplex_rpc')
	print(await stub('test ', suffix='passed!'))

	handle = stub.async_call(('test ', ), {'suffix':'passed!', })
	print(handle.join())
	print(await stub.coro_call(('test ', ), {'suffix':'passed!', }))
	print(stub.sync_call(('test ', ), {'suffix':'passed!', }))

async def test_SyncDuplexStub():
	print('test_SyncDuplexStub')

	stub = axon.duplex_stubs.SyncDuplexStub(worker_ip='localhost', rpc_name='duplex_rpc')
	print(stub('test ', suffix='passed!'))

	handle = stub.async_call(('test ', ), {'suffix':'passed!', })
	print(handle.join())
	print(await stub.coro_call(('test ', ), {'suffix':'passed!', }))
	print(stub.sync_call(('test ', ), {'suffix':'passed!', }))

# gotta set up a worker to test the stubs on

@axon.worker.rpc(comms_pattern='duplex')
def duplex_rpc(prefix, suffix=' test failed'):
	return prefix+suffix

worker_thread = threading.Thread(target=axon.worker.init, name='client_test.worker_thread', daemon=True)
worker_thread.daemon = True

async def main():
	print('starting worker thread for testing stubs against')
	worker_thread.start()

	time.sleep(1)

	test_async_stub()

	await test_coro_stub()

	test_sync_stub()

	# await test_GenericDuplexStub()

	# await test_AsyncDuplexStub()
	# await test_CoroDuplexStub()
	# await test_SyncDuplexStub()

if (__name__ == '__main__'): asyncio.run(main())