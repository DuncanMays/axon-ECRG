class ObjectClass():

	def __init__(self):
		self.attribute1 = "attribute1"


	def newAttr(self, name, attr):
		print('what')
		setattr(self, name, attr)


objectClass = ObjectClass()
print(objectClass.attribute1)

objectClass.newAttr("newAttribute", "new attr")
print(objectClass.newAttribute)