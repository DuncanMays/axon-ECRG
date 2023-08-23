
class TestClass1():
	def __init__(self):
		pass

	def fn(self):
		return 'TestClass1'

class TestClass2():
	def __init__(self):
		pass

	def fn(self):
		return 'TestClass2'

fn = lambda self : 'Lambda fn'

T = type('MetaClass', (TestClass2, TestClass1), {'fn': fn})

t = T()

print(t.fn())