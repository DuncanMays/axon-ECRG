from threading import Lock

class InlineExecutor():

	def __init__(self):
		self.inline_lock = Lock()

	def submit(self, target, args, kwargs):
		result = None
		with self.inline_lock:
			result = target(args, kwargs)
		return result
