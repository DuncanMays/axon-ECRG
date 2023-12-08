from threading import Lock
from concurrent.futures import Future

class InlineExecutor():

	def __init__(self):
		self.inline_lock = Lock()

	def submit(self, target, args, kwargs):
		result_future = Future()

		with self.inline_lock:
			result_future.set_result(target(args, kwargs))

		return result_future
