from sys import path
path.append('..')
import axon

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

worker_thread = threading.Thread(target=axon.worker.init, name='client_test.worker_thread')
worker_thread.daemon = True

async def test_RemoteWorker():
	print('test_RemoteWorker')

	w = axon.client.RemoteWorker('localhost')

	print(await w.rpcs.simplex_rpc('simplex test ', suffix='passed'))
	print(await w.rpcs.duplex_rpc('duplex test ', suffix='passed'))

async def main():
	worker_thread.start()

	# waits for the worker's flask app to start
	await asyncio.sleep(0.5)

	await test_RemoteWorker()

asyncio.run(main())