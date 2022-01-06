class InlineExecutor():

	def __init__(self, target=lambda x : x, args=('null',)):
		self.target = target
		self.args = args

	def start(self):
		self.target(*self.args)

	def join(self):
		pass