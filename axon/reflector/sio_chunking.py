from math import ceil

CHUNK_SIZE = 100_000


def sio_send(sio, event, message, **emit_kwargs):
	"""Send a SocketIO message, chunking if it exceeds CHUNK_SIZE.

	message must be formatted as '{call_ID}|{...rest...}'. If small enough,
	emits event with the full message. Otherwise splits into numbered chunks
	and emits '{event}_chunk' for each.

	Chunk envelope format: '{chunk_num}|{num_chunks}|{call_ID}|{chunk_data}'
	"""
	call_ID = message.split('|', 1)[0]

	if len(message) < CHUNK_SIZE:
		sio.emit(event, data=message, **emit_kwargs)

	else:
		chunk_event = event + '_chunk'
		num_chunks = ceil(len(message) / CHUNK_SIZE)

		for i in range(num_chunks):
			chunk = message[CHUNK_SIZE * i: CHUNK_SIZE * (i + 1)]
			sio.emit(chunk_event, data=f'{i}|{num_chunks}|{call_ID}|{chunk}', **emit_kwargs)


class ChunkBuffer:
	"""Accumulates numbered SocketIO chunks and returns the complete message when all are received.

	Usage:
		buf = ChunkBuffer()

		# in a chunk event handler:
		assembled = buf.receive(event_str)
		if assembled is not None:
			# assembled has the same '{call_ID}|{...}' format as sio_send's message argument
			handle(assembled)
	"""

	def __init__(self):
		self._buffers = {}

	def receive(self, event_str):
		"""Process a chunk event string.

		Chunk envelope format: '{chunk_num}|{num_chunks}|{call_ID}|{chunk_data}'

		Returns the complete reassembled message when all chunks have arrived, else None.
		"""
		chunk_num, num_chunks, call_ID, chunk_str = event_str.split('|', 3)
		chunk_num = int(chunk_num)
		num_chunks = int(num_chunks)

		if call_ID not in self._buffers:
			self._buffers[call_ID] = []

		self._buffers[call_ID].append((chunk_num, chunk_str))

		if len(self._buffers[call_ID]) == num_chunks:
			chunks = sorted(self._buffers.pop(call_ID))
			return ''.join(data for _, data in chunks)

		return None
