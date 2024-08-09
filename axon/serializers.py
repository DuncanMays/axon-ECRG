import pickle
import codecs

# pickle operates on bytes, but http operates on strings, so we've gotta convert pickles to and from a string
def serialize(obj):
	pickled = pickle.dumps(obj)
	return codecs.encode(pickled, "base64").decode()

# pickle operates on bytes, but http operates on strings, so we've gotta convert pickles to and from a string
def deserialize(obj_str):
	# print(obj_str)
	obj_bytes = codecs.decode(obj_str.encode(), "base64")
	# print(pickle.loads(obj_bytes))
	return pickle.loads(obj_bytes)