import pickle
import codecs

from abc import ABC

# pickle operates on bytes, but http operates on strings, so we've gotta convert pickles to and from a string
def serialize(obj):
	pickled = pickle.dumps(obj)
	return codecs.encode(pickled, "base64").decode()

# pickle operates on bytes, but http operates on strings, so we've gotta convert pickles to and from a string
def deserialize(obj_str):
	obj_bytes = codecs.decode(obj_str.encode(), "base64")
	return pickle.loads(obj_bytes)

class AbstractSerializer(ABC):

	def __init__(self):
		self._serialize = serialize
		self._deserialize = deserialize

	@property
	def serialize(self):
		return self._serialize

	@serialize.setter
	def serialize(self, value):
		self._serialize = value

	@property
	def deserialize(self):
		return self._deserialize

	@deserialize.setter
	def deserialize(self, value):
		self._deserialize = value