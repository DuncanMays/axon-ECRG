from axon.serializers import serialize

log_file = './reflector.log'


def passthrough_serialize(params):

	if params == ((), {}):
		return serialize(((), {}))

	if '__profile_flag__' in params:
		return serialize(params)

	return params[0][0]


def passthrough_deserialize(input_str):

	if input_str == serialize(((), {})):
		return ((), {})

	return (input_str,), {}
