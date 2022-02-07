from sys import path
path.append('..')
from axon import return_value_linker
import threading
import time
import asyncio

async def test_ReturnEvent_coro():
	print('test_ReturnEvent_coro')

	event_loop = asyncio.get_running_loop()
	event = return_value_linker.ReturnEvent_coro()

	def thread_fn(event_loop):
		
		def callback():
			print('putting return value')
			event.put_return_value('great success!')

		event_loop.call_soon_threadsafe(callback)

	t = threading.Thread(target=thread_fn, args=(event_loop, ))
	t.daemon = True
	t.start()

	print('awaiting return value')
	print('return value attained:', await event.get_return_value())

def test_ReturnEvent_async():
	print('test_ReturnEvent_async')

	event = return_value_linker.ReturnEvent_async()

	def thread_fn():
		
		def callback():
			print('putting return value')
			event.put_return_value('great success!')

		callback()

	t = threading.Thread(target=thread_fn)
	t.daemon = True
	t.start()

	print('awaiting return value')
	print('return value attained:', event.get_return_value())

async def test_RVL():
	loop = asyncio.get_running_loop()
	rvl = return_value_linker.RVL(loop)
	rvl.start()

	pass

async def main():
	await test_ReturnEvent_coro()

	test_ReturnEvent_async()

if (__name__ == '__main__'): asyncio.run(main())
