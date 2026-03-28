
termination_str = 'End of message'

def send_in_chunks(socket, input_str, chunk_size=100_000):

	for i in range(len(input_str)//chunk_size):
		chunk = input_str[ chunk_size*i : chunk_size*(i+1) ]
		socket.send(chunk)

	socket.send(input_str[chunk_size*(len(input_str)//chunk_size):])
	socket.send(termination_str)

def recv_chunks(socket):

	result_str = ''
	while True:
		chunk = socket.recv()

		if (chunk == termination_str):
			break

		else:
			result_str += chunk

	return result_str