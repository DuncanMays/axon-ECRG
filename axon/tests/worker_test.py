import axon
import asyncio
import time
import threading
import multiprocessing
import inspect
import pytest

from itertools import product
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

url_scheme = axon.config.url_scheme
message = 'hello world!'

start_delay = 2*0.05
small_delay = 2*0.05
big_delay = 2*0.5

class PoolTestService():
	async def print_this_async(self, delay, message):
		loop = asyncio.get_event_loop()
		await asyncio.sleep(delay)
		return message

	def print_this(self, delay, message):
		time.sleep(delay)
		return message

@pytest.fixture(scope='package')
def fix_pool_services():
	ils = PoolTestService()
	axon.worker.service(ils, name='inline_service')

	tps = PoolTestService()
	tpe = ThreadPoolExecutor(max_workers=10)
	axon.worker.service(tps, name='thread_pool_service', executor=tpe)

	tps = PoolTestService()
	ppe = ProcessPoolExecutor(max_workers=10, mp_context=multiprocessing.get_context("spawn"))
	axon.worker.service(tps, name='process_pool_service', executor=ppe)

@pytest.mark.tl
@pytest.mark.asyncio
async def test_invokation(fix_pool_services):
	remote_worker = axon.client.get_stub(f'{url_scheme}://localhost:{axon.config.transport.config.port}')
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
async def test_inline_concurrency(fix_pool_services):
	# tests that non async services with the inline executor do not run in parallel

	inline_service = axon.client.get_stub(f'localhost:/inline_service')
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
async def test_service_concurrency(fix_pool_services):
	# this function tests to see if calls to services run in executors can be run in parallel
	
	endpoints = list(product(['thread_pool_service', 'process_pool_service'], ['print_this', 'print_this_async']))
	# the async version of print_this should run in parallel, even with the inline executor
	endpoints.append(('inline_service', 'print_this_async'))
	services = [axon.client.get_stub(f'localhost/{name}/{v}') for name, v in endpoints]

	for s in services:
		print(s.url)
		await verify_parallel(s)
