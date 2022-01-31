from threading import Lock

# this is so that no other inline functions will execute when an inline duplex RPC is running, since it must run in a separate thread
inline_lock = Lock()

class InlineExecutor():

	def __init__(self, target=lambda x : x, args=('null',)):
		self.target = target
		self.args = args

	def start(self):
		with inline_lock:
			self.target(*self.args)

	def join(self):
		pass