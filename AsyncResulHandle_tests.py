from axon.transport_client import AsyncResultHandle
from concurrent.futures import ThreadPoolExecutor
import asyncio, time

def sync_delay(delay):
	print(f'starting sync delay {delay}')
	time.sleep(delay)
	print(f'sync delay {delay} completed')

	return 'sync delay return value'

async def async_delay(delay):
	print(f'starting async delay {delay}')
	await asyncio.sleep(delay)
	print(f'async delay {delay} completed')

async def main():
	print('main')

	e = ThreadPoolExecutor(max_workers=10)

	# long_f = e.submit(sync_delay, 2)
	# short_f = e.submit(sync_delay, 0.1)

	# long_rh = AsyncResultHandle(long_f)
	# short_rh = AsyncResultHandle(short_f)

	# l = [long_rh, short_rh]
	# await asyncio.gather(*l)

	# --------------------------

	# f = e.submit(sync_delay, 1)

	# l = [AsyncResultHandle(f), async_delay(0.1)]
	# await asyncio.gather(*l)

	# --------------------------

	# loop = asyncio.get_event_loop()
	# a = loop.run_in_executor(e, sync_delay, 2)
	# b = loop.run_in_executor(e, sync_delay, 0.1)
	# await asyncio.gather(a, b)

	# --------------------------

	# a = AsyncResultHandle(sync_delay, 1)

	# loop = asyncio.get_event_loop()
	# print(id(loop))
	# print(loop.is_closed())
	# await a
	# a.join()
	# print(loop.is_closed())

	# --------------------------

	# class TestCoro():

	# 	def __init__(self):
	# 		pass

	# 	def __await__(self):
	# 		print('__await__')
	# 		yield
	# 		loop = asyncio.get_event_loop()
	# 		return loop.run_in_executor(e, sync_delay, 1)

	# 	def __call__(self):
	# 		print('__call__')

	# t = TestCoro()

	# t()
	# t = await t
	# await t

	# loop = asyncio.get_event_loop()
	# t = loop.run_in_executor(e, sync_delay, 1)

	# print(t)
	# print(dir(t))
	# # print(t.result())
	# print(t.done())
	# # print(await t)
	# print(next(t.__await__()))
	# print(next(t.__await__()))

	# --------------------------

	class AsyncResult():

		def __init__(self):
			
			# self.__await__ = self.coro.__await__
			pass

		def __await__(self):
			loop = asyncio.get_event_loop()
			self.coro = loop.run_in_executor(e, sync_delay, 1)
			return self.coro.__await__()

	a = AsyncResult()
	print(a)
	await a

	print('all done')

asyncio.run(main())