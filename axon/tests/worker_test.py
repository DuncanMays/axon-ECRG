import axon
import asyncio
import time
import threading
import inspect
import pytest

url_scheme = axon.config.url_scheme
time_safety_magin = 0.1

big_delay = 0.5
message = 'hello world!'

# @pytest.mark.tl
# @pytest.mark.asyncio
# async def test_invokation():
# 	remote_worker = axon.client.get_RemoteWorker(f'{url_scheme}://localhost:{axon.config.transport.config.port}')
# 	message = 'hello world!'
# 	delay = 0

# 	assert(await remote_worker.inline_service.print_this(delay, message) == message)
# 	assert(await remote_worker.thread_pool_service.print_this(delay, message) == message)
# 	assert(await remote_worker.process_pool_service.print_this(delay, message) == message)

# 	assert(await remote_worker.inline_service.print_this_async(delay, message) == message)
# 	assert(await remote_worker.thread_pool_service.print_this_async(delay, message) == message)
# 	assert(await remote_worker.process_pool_service.print_this_async(delay, message) == message)

# 	print('test_invokation complete!')

# @pytest.mark.tl
# @pytest.mark.asyncio
# async def test_inline_concurrency():
# 	inline_service = axon.client.get_ServiceStub(f'{url_scheme}://localhost:{axon.config.transport.config.port}/inline_service')
# 	completion_order = []

# 	async def long_coro():
# 		await inline_service.print_this(big_delay, message)
# 		completion_order.append('long_coro')

# 	async def short_coro():
# 		await inline_service.print_this(0, message)
# 		completion_order.append('short_coro')

# 	reqs = [long_coro(), short_coro()]
# 	await asyncio.gather(*reqs)

# 	assert(completion_order[0] == 'long_coro')
# 	assert(completion_order[1] == 'short_coro')

@pytest.mark.tl
@pytest.mark.asyncio
async def test_tpe_concurrency():
	thread_pool_service = axon.client.get_ServiceStub(f'{url_scheme}://localhost:{axon.config.transport.config.port}/thread_pool_service')
	completion_order = []

	async def long_coro():
		print('long_coro started')
		await thread_pool_service.print_this(2, message)
		# await thread_pool_service.print_this(2, message).join()
		completion_order.append('long_coro')
		print('long_coro ended')

	async def short_coro():
		print('short_coro started')
		await thread_pool_service.print_this(0.1, message)
		# await thread_pool_service.print_this(0.1, message).join()
		completion_order.append('short_coro')
		print('short_coro ended')

	reqs = [long_coro(), short_coro()]
	await asyncio.gather(*reqs)

	assert(completion_order[0] == 'short_coro')
	assert(completion_order[1] == 'long_coro')

	# message = 'hello world!'
	# delay = 1

	# start = time.time()

	# reqs = []
	# reqs.append(thread_pool_service.print_this(delay, message))
	# reqs.append(thread_pool_service.print_this(delay, message))

	# reqs = await asyncio.gather(*reqs)

	# end = time.time()
	# delay = end - start

	# assert(abs(delay - 1) < time_safety_magin)
	# print('test_tpe_concurrency complete!')

# @pytest.mark.tl
# @pytest.mark.asyncio
# async def test_ppe_concurrency():
# 	process_pool_service = axon.client.get_ServiceStub(f'{url_scheme}://localhost:{axon.config.transport.config.port}/process_pool_service')
# 	message = 'hello world!'
# 	delay = 1

# 	start = time.time()

# 	reqs = []
# 	reqs.append(process_pool_service.print_this(delay, message))
# 	reqs.append(process_pool_service.print_this(delay, message))

# 	reqs = await asyncio.gather(*reqs)

# 	end = time.time()
# 	delay = end - start

# 	assert(abs(delay - 1) < time_safety_magin)
# 	print('test_ppe_concurrency complete!')

# @pytest.mark.tl
# @pytest.mark.asyncio
# async def test_inline_async_concurrency():
# 	inline_service = axon.client.get_ServiceStub(f'{url_scheme}://localhost:{axon.config.transport.config.port}/inline_service')
# 	message = 'hello world!'
# 	delay = 1

# 	start = time.time()

# 	reqs = []
# 	reqs.append(inline_service.print_this_async(delay, message))
# 	reqs.append(inline_service.print_this_async(delay, message))

# 	reqs = await asyncio.gather(*reqs)

# 	end = time.time()
# 	delay = end - start

# 	assert(abs(delay - 1) < time_safety_magin)
# 	print('test_inline_async_concurrency complete!')

# @pytest.mark.tl
# @pytest.mark.asyncio
# async def test_tpe_async_concurrency():
# 	thread_pool_service = axon.client.get_ServiceStub(f'{url_scheme}://localhost:{axon.config.transport.config.port}/thread_pool_service')
# 	message = 'hello world!'
# 	delay = 1

# 	start = time.time()

# 	reqs = []
# 	reqs.append(thread_pool_service.print_this_async(delay, message))
# 	reqs.append(thread_pool_service.print_this_async(delay, message))

# 	reqs = await asyncio.gather(*reqs)

# 	end = time.time()
# 	delay = end - start

# 	assert(abs(delay - 1) < time_safety_magin)
# 	print('test_tpe_async_concurrency complete!')

# @pytest.mark.tl
# @pytest.mark.asyncio
# async def test_ppe_async_concurrency():
# 	process_pool_service = axon.client.get_ServiceStub(f'{url_scheme}://localhost:{axon.config.transport.config.port}/process_pool_service')
# 	message = 'hello world!'
# 	delay = 1

# 	start = time.time()

# 	reqs = []
# 	reqs.append(process_pool_service.print_this_async(delay, message))
# 	reqs.append(process_pool_service.print_this_async(delay, message))

# 	reqs = await asyncio.gather(*reqs)

# 	end = time.time()
# 	delay = end - start

# 	assert(abs(delay - 1) < time_safety_magin)
# 	print('test_ppe_async_concurrency complete!')
