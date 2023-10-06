from sys import path
path.append('..')
from axon import return_value_linker
import threading
import asyncio
import pytest

@pytest.mark.asyncio
async def test_ReturnEvent_coro():
	print('test_ReturnEvent_coro')

	event = return_value_linker.ReturnEvent_coro()
	await event.init()

	def thread_fn():
		print('putting return value')
		event.put_return_value('great success!')

	t = threading.Thread(target=thread_fn, name='axon/tests/return_value_linker_test/test_ReturnEvent_coro')
	t.daemon = True
	t.start()

	print('awaiting return value')
	print('return value attained:', await event.get_return_value())

def test_ReturnEvent_async():
	print('test_ReturnEvent_async')

	event = return_value_linker.ReturnEvent_async()

	def thread_fn():
		print('putting return value')
		event.put_return_value('great success!')

	t = threading.Thread(target=thread_fn, name='axon/tests/return_value_linker_test/test_ReturnEvent_async')
	t.daemon = True
	t.start()

	print('awaiting return value')
	print('return value attained:', event.get_return_value())
