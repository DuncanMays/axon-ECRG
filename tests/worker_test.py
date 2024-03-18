from sys import path
path.append('..')

import axon
import asyncio
import time
import threading
import inspect
import pytest

url_scheme = axon.config.url_scheme
time_safety_magin = 0.1

@pytest.mark.asyncio
async def test_invokation():
	remote_worker = axon.client.get_RemoteWorker(f'{url_scheme}://localhost:{axon.config.comms_config.worker_port}')
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
	inline_service = axon.client.get_ServiceStub(f'{url_scheme}://localhost:{axon.config.comms_config.worker_port}/inline_service')
	message = 'hello world!'
	delay = 1

	start = time.time()

	reqs = []
	reqs.append(inline_service.print_this(delay, message))
	reqs.append(inline_service.print_this(delay, message))

	reqs = await asyncio.gather(*reqs)

	end = time.time()
	delay = end - start

	assert(abs(delay - 2) < time_safety_magin)
	print('test_inline_concurrency complete!')

@pytest.mark.asyncio
async def test_tpe_concurrency():
	thread_pool_service = axon.client.get_ServiceStub(f'{url_scheme}://localhost:{axon.config.comms_config.worker_port}/thread_pool_service')
	message = 'hello world!'
	delay = 1

	start = time.time()

	reqs = []
	reqs.append(thread_pool_service.print_this(delay, message))
	reqs.append(thread_pool_service.print_this(delay, message))

	reqs = await asyncio.gather(*reqs)

	end = time.time()
	delay = end - start

	assert(abs(delay - 1) < time_safety_magin)
	print('test_tpe_concurrency complete!')

@pytest.mark.asyncio
async def test_ppe_concurrency():
	process_pool_service = axon.client.get_ServiceStub(f'{url_scheme}://localhost:{axon.config.comms_config.worker_port}/process_pool_service')
	message = 'hello world!'
	delay = 1

	start = time.time()

	reqs = []
	reqs.append(process_pool_service.print_this(delay, message))
	reqs.append(process_pool_service.print_this(delay, message))

	reqs = await asyncio.gather(*reqs)

	end = time.time()
	delay = end - start

	assert(abs(delay - 1) < time_safety_magin)
	print('test_ppe_concurrency complete!')

@pytest.mark.asyncio
async def test_inline_async_concurrency():
	inline_service = axon.client.get_ServiceStub(f'{url_scheme}://localhost:{axon.config.comms_config.worker_port}/inline_service')
	message = 'hello world!'
	delay = 1

	start = time.time()

	reqs = []
	reqs.append(inline_service.print_this_async(delay, message))
	reqs.append(inline_service.print_this_async(delay, message))

	reqs = await asyncio.gather(*reqs)

	end = time.time()
	delay = end - start

	assert(abs(delay - 1) < time_safety_magin)
	print('test_inline_async_concurrency complete!')

@pytest.mark.asyncio
async def test_tpe_async_concurrency():
	thread_pool_service = axon.client.get_ServiceStub(f'{url_scheme}://localhost:{axon.config.comms_config.worker_port}/thread_pool_service')
	message = 'hello world!'
	delay = 1

	start = time.time()

	reqs = []
	reqs.append(thread_pool_service.print_this_async(delay, message))
	reqs.append(thread_pool_service.print_this_async(delay, message))

	reqs = await asyncio.gather(*reqs)

	end = time.time()
	delay = end - start

	assert(abs(delay - 1) < time_safety_magin)
	print('test_tpe_async_concurrency complete!')

@pytest.mark.asyncio
async def test_ppe_async_concurrency():
	process_pool_service = axon.client.get_ServiceStub(f'{url_scheme}://localhost:{axon.config.comms_config.worker_port}/process_pool_service')
	message = 'hello world!'
	delay = 1

	start = time.time()

	reqs = []
	reqs.append(process_pool_service.print_this_async(delay, message))
	reqs.append(process_pool_service.print_this_async(delay, message))

	reqs = await asyncio.gather(*reqs)

	end = time.time()
	delay = end - start

	assert(abs(delay - 1) < time_safety_magin)
	print('test_ppe_async_concurrency complete!')
