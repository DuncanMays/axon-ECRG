from threading import Lock

# this is so that no other inline functions will execute when an inline duplex RPC is running
# Inline duplex RPCs need to run in a separate thread because of WSGI, which mandates that a route stops executing once it has sent its response, preventing duplex RPCs from sending a return POST
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