import axon
import asyncio
import time
import threading
import inspect
import pytest

from itertools import product

url_scheme = axon.config.url_scheme
message = 'hello world!'

start_delay = 0.01
small_delay = 0.01
big_delay = 0.1

@pytest.mark.tl
@pytest.mark.asyncio
async def test_invokation():
	remote_worker = axon.client.get_RemoteWorker(f'{url_scheme}://localhost:{axon.config.transport.config.port}')
	delay = 0

	assert(await remote_worker.inline_service.print_this(delay, message) == message)
	assert(await remote_worker.thread_pool_service.print_this(delay, message) == message)
	assert(await remote_worker.process_pool_service.print_this(delay, message) == message)

	assert(await remote_worker.inline_service.print_this_async(delay, message) == message)
	assert(await remote_worker.thread_pool_service.print_this_async(delay, message) == message)
	assert(await remote_worker.process_pool_service.print_this_async(delay, message) == message)

	print('test_invokation complete!')

@pytest.mark.tl
@pytest.mark.asyncio
async def test_inline_concurrency():
	# tests that non async services with the inline executor do not run in parallel
	
	inline_service = axon.client.get_ServiceStub(f'localhost:/inline_service')
	completion_order = []

	async def long_coro():
		await inline_service.print_this(big_delay, 'inline')
		completion_order.append('long_coro')

	async def short_coro():
		time.sleep(start_delay)
		await inline_service.print_this(small_delay, 'inline')
		completion_order.append('short_coro')

	reqs = [long_coro(), short_coro()]
	await asyncio.gather(*reqs)

	assert(completion_order[0] == 'long_coro')
	assert(completion_order[1] == 'short_coro')

async def verify_parallel(service):
	# this function tests if calls to a service can be run in parallel by making two calls, a long call, and a short call within that one. If the short call finishes first despite starting last, the test passes

	completion_order = []

	async def long_coro():
		await service(big_delay, message)
		completion_order.append('long_coro')

	async def short_coro():
		time.sleep(start_delay)
		await service(small_delay, message)
		completion_order.append('short_coro')

	reqs = [long_coro(), short_coro()]
	await asyncio.gather(*reqs)

	assert(completion_order[0] == 'short_coro')
	assert(completion_order[1] == 'long_coro')

@pytest.mark.tl
@pytest.mark.asyncio
async def test_service_concurrency():
	# this function tests to see if calls to services run in executors can be run in parallel
	
	endpoints = list(product(['thread_pool_service', 'process_pool_service'], ['print_this', 'print_this_async']))
	# the async version of print_this should run in parallel, even with the inline executor
	endpoints.append(('inline_service', 'print_this_async'))
	services = [axon.client.get_ServiceStub(f'localhost/{name}/{v}') for name, v in endpoints]

	for s in services:
		await verify_parallel(s)
