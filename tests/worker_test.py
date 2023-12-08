# import pytest

from sys import path
path.append('..')

import axon
import asyncio
import time
import threading
import inspect

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

port = 5000
max_workers = 10

tpe = ThreadPoolExecutor(max_workers=10)
ppe = ProcessPoolExecutor(max_workers=10)

@axon.worker.rpc()
async def print_this_async_ie(message):
	await asyncio.sleep(1)
	return message

@axon.worker.rpc()
def print_this_ie(message):
	return message

@axon.worker.rpc(executor=tpe)
async def print_this_async_tpe(message):
	await asyncio.sleep(1)
	return message

@axon.worker.rpc(executor=tpe)
def print_this_tpe(message):
	return message

@axon.worker.rpc(executor=ppe)
async def print_this_async_ppe(message):
	await asyncio.sleep(1)
	return message

@axon.worker.rpc(executor=ppe)
def print_this_ppe(message):
	return message

async def main():
	worker_thread = threading.Thread(target=axon.worker.init, kwargs={'port':port}, daemon=True)
	worker_thread.start()
	await asyncio.sleep(1)

	remote_worker = axon.client.get_RemoteWorker('localhost', port=port)

	message = 'hello world!'

	assert(await remote_worker.rpcs.print_this_ie(message) == message)
	assert(await remote_worker.rpcs.print_this_tpe(message) == message)
	assert(await remote_worker.rpcs.print_this_ppe(message) == message)

	assert(await remote_worker.rpcs.print_this_async_ie(message) == message)
	assert(await remote_worker.rpcs.print_this_async_tpe(message) == message)
	assert(await remote_worker.rpcs.print_this_async_ppe(message) == message)

	print('test complete!')

	

asyncio.run(main())
