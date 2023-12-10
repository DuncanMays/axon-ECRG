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
time_safety_magin = 0.1

tpe = ThreadPoolExecutor(max_workers=10)
ppe = ProcessPoolExecutor(max_workers=10)

@axon.worker.rpc()
async def print_this_async_ie(delay, message):
	loop = asyncio.get_event_loop()
	print(loop)
	print(id(loop))
	await asyncio.sleep(delay)
	return message

@axon.worker.rpc()
def print_this_ie(delay, message):
	time.sleep(delay)
	return message

@axon.worker.rpc(executor=tpe)
async def print_this_async_tpe(delay, message):
	loop = asyncio.get_event_loop()
	print(loop)
	print(id(loop))
	await asyncio.sleep(delay)
	return message

@axon.worker.rpc(executor=tpe)
def print_this_tpe(delay, message):
	time.sleep(delay)
	return message

@axon.worker.rpc(executor=ppe)
async def print_this_async_ppe(delay, message):
	loop = asyncio.get_event_loop()
	print(loop)
	print(id(loop))
	await asyncio.sleep(delay)
	return message

@axon.worker.rpc(executor=ppe)
def print_this_ppe(delay, message):
	time.sleep(delay)
	return message

async def test_invokation():
	remote_worker = axon.client.get_RemoteWorker('localhost', port=port)
	message = 'hello world!'
	delay = 0

	assert(await remote_worker.rpcs.print_this_ie(delay, message) == message)
	assert(await remote_worker.rpcs.print_this_tpe(delay, message) == message)
	assert(await remote_worker.rpcs.print_this_ppe(delay, message) == message)

	assert(await remote_worker.rpcs.print_this_async_ie(delay, message) == message)
	assert(await remote_worker.rpcs.print_this_async_tpe(delay, message) == message)
	assert(await remote_worker.rpcs.print_this_async_ppe(delay, message) == message)

	print('test_invokation complete!')


async def test_inline_concurrency():
	remote_worker = axon.client.get_RemoteWorker('localhost', port=port)
	message = 'hello world!'
	delay = 1

	start = time.time()

	reqs = []
	reqs.append(remote_worker.rpcs.print_this_ie(delay, message))
	reqs.append(remote_worker.rpcs.print_this_ie(delay, message))

	reqs = await asyncio.gather(*reqs)

	end = time.time()
	delay = end - start

	assert(abs(delay - 2) < time_safety_magin)
	print('test_inline_concurrency complete!')

async def test_tpe_concurrency():
	remote_worker = axon.client.get_RemoteWorker('localhost', port=port)
	message = 'hello world!'
	delay = 1

	start = time.time()

	reqs = []
	reqs.append(remote_worker.rpcs.print_this_tpe(delay, message))
	reqs.append(remote_worker.rpcs.print_this_tpe(delay, message))

	reqs = await asyncio.gather(*reqs)

	end = time.time()
	delay = end - start

	assert(abs(delay - 1) < time_safety_magin)
	print('test_tpe_concurrency complete!')

async def test_ppe_concurrency():
	remote_worker = axon.client.get_RemoteWorker('localhost', port=port)
	message = 'hello world!'
	delay = 1

	start = time.time()

	reqs = []
	reqs.append(remote_worker.rpcs.print_this_ppe(delay, message))
	reqs.append(remote_worker.rpcs.print_this_ppe(delay, message))

	reqs = await asyncio.gather(*reqs)

	end = time.time()
	delay = end - start

	assert(abs(delay - 1) < time_safety_magin)
	print('test_ppe_concurrency complete!')

async def test_inline_async_concurrency():
	remote_worker = axon.client.get_RemoteWorker('localhost', port=port)
	message = 'hello world!'
	delay = 1

	start = time.time()

	reqs = []
	reqs.append(remote_worker.rpcs.print_this_async_ie(delay, message))
	reqs.append(remote_worker.rpcs.print_this_async_ie(delay, message))

	reqs = await asyncio.gather(*reqs)

	end = time.time()
	delay = end - start

	assert(abs(delay - 1) < time_safety_magin)
	print('test_inline_async_concurrency complete!')

async def test_tpe_async_concurrency():
	remote_worker = axon.client.get_RemoteWorker('localhost', port=port)
	message = 'hello world!'
	delay = 1

	start = time.time()

	reqs = []
	reqs.append(remote_worker.rpcs.print_this_async_tpe(delay, message))
	reqs.append(remote_worker.rpcs.print_this_async_tpe(delay, message))

	reqs = await asyncio.gather(*reqs)

	end = time.time()
	delay = end - start

	assert(abs(delay - 1) < time_safety_magin)
	print('test_tpe_async_concurrency complete!')

async def test_ppe_async_concurrency():
	remote_worker = axon.client.get_RemoteWorker('localhost', port=port)
	message = 'hello world!'
	delay = 1

	start = time.time()

	reqs = []
	reqs.append(remote_worker.rpcs.print_this_async_ppe(delay, message))
	reqs.append(remote_worker.rpcs.print_this_async_ppe(delay, message))

	reqs = await asyncio.gather(*reqs)

	end = time.time()
	delay = end - start

	assert(abs(delay - 1) < time_safety_magin)
	print('test_ppe_async_concurrency complete!')

async def main():
	worker_thread = threading.Thread(target=axon.worker.init, kwargs={'port':port}, daemon=True)
	worker_thread.start()
	await asyncio.sleep(1)

	await test_invokation()
	await test_inline_concurrency()
	await test_tpe_concurrency()
	await test_ppe_concurrency()
	await test_inline_async_concurrency()
	await test_tpe_async_concurrency()
	await test_ppe_async_concurrency()

asyncio.run(main())
