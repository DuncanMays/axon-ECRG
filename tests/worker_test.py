from sys import path
path.append('..')

import axon
import asyncio
import time
import threading
import inspect
import pytest

time_safety_magin = 0.1

@pytest.mark.asyncio
async def test_invokation():
	remote_worker = axon.client.get_RemoteWorker('localhost')
	message = 'hello world!'
	delay = 0

	assert(await remote_worker.inline_service.print_this(delay, message) == message)
	assert(await remote_worker.thread_pool_service.print_this(delay, message) == message)
	assert(await remote_worker.process_pool_service.print_this(delay, message) == message)

	assert(await remote_worker.inline_service.print_this_async(delay, message) == message)
	assert(await remote_worker.thread_pool_service.print_this_async(delay, message) == message)
	assert(await remote_worker.process_pool_service.print_this_async(delay, message) == message)

	print('test_invokation complete!')


@pytest.mark.asyncio
async def test_inline_concurrency():
	remote_worker = axon.client.get_RemoteWorker('localhost')
	message = 'hello world!'
	delay = 1

	start = time.time()

	reqs = []
	reqs.append(remote_worker.inline_service.print_this(delay, message))
	reqs.append(remote_worker.inline_service.print_this(delay, message))

	reqs = await asyncio.gather(*reqs)

	end = time.time()
	delay = end - start

	assert(abs(delay - 2) < time_safety_magin)
	print('test_inline_concurrency complete!')

@pytest.mark.asyncio
async def test_tpe_concurrency():
	remote_worker = axon.client.get_RemoteWorker('localhost')
	message = 'hello world!'
	delay = 1

	start = time.time()

	reqs = []
	reqs.append(remote_worker.thread_pool_service.print_this(delay, message))
	reqs.append(remote_worker.thread_pool_service.print_this(delay, message))

	reqs = await asyncio.gather(*reqs)

	end = time.time()
	delay = end - start

	assert(abs(delay - 1) < time_safety_magin)
	print('test_tpe_concurrency complete!')

@pytest.mark.asyncio
async def test_ppe_concurrency():
	remote_worker = axon.client.get_RemoteWorker('localhost')
	message = 'hello world!'
	delay = 1

	start = time.time()

	reqs = []
	reqs.append(remote_worker.process_pool_service.print_this(delay, message))
	reqs.append(remote_worker.process_pool_service.print_this(delay, message))

	reqs = await asyncio.gather(*reqs)

	end = time.time()
	delay = end - start

	assert(abs(delay - 1) < time_safety_magin)
	print('test_ppe_concurrency complete!')

@pytest.mark.asyncio
async def test_inline_async_concurrency():
	remote_worker = axon.client.get_RemoteWorker('localhost')
	message = 'hello world!'
	delay = 1

	start = time.time()

	reqs = []
	reqs.append(remote_worker.inline_service.print_this_async(delay, message))
	reqs.append(remote_worker.inline_service.print_this_async(delay, message))

	reqs = await asyncio.gather(*reqs)

	end = time.time()
	delay = end - start

	assert(abs(delay - 1) < time_safety_magin)
	print('test_inline_async_concurrency complete!')

@pytest.mark.asyncio
async def test_tpe_async_concurrency():
	remote_worker = axon.client.get_RemoteWorker('localhost')
	message = 'hello world!'
	delay = 1

	start = time.time()

	reqs = []
	reqs.append(remote_worker.thread_pool_service.print_this_async(delay, message))
	reqs.append(remote_worker.thread_pool_service.print_this_async(delay, message))

	reqs = await asyncio.gather(*reqs)

	end = time.time()
	delay = end - start

	assert(abs(delay - 1) < time_safety_magin)
	print('test_tpe_async_concurrency complete!')

@pytest.mark.asyncio
async def test_ppe_async_concurrency():
	remote_worker = axon.client.get_RemoteWorker('localhost')
	message = 'hello world!'
	delay = 1

	start = time.time()

	reqs = []
	reqs.append(remote_worker.process_pool_service.print_this_async(delay, message))
	reqs.append(remote_worker.process_pool_service.print_this_async(delay, message))

	reqs = await asyncio.gather(*reqs)

	end = time.time()
	delay = end - start

	assert(abs(delay - 1) < time_safety_magin)
	print('test_ppe_async_concurrency complete!')
