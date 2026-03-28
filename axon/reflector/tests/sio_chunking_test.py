import pytest
from axon.reflector.sio_chunking import sio_send, ChunkBuffer, CHUNK_SIZE


# --- helpers ---

def make_emit_recorder():
	"""Returns a list and an emit callable that appends (event, data) to it."""
	calls = []
	def emit(event, data):
		calls.append((event, data))
	return calls, emit


def send_via_buffer(message, call_ID='id1', shuffle=False):
	"""Round-trip helper: sends message through sio_send, feeds all emitted
	events into a ChunkBuffer, and returns the final assembled result."""
	calls, emit = make_emit_recorder()
	sio_send(emit, 'rpc_result', message)

	buf = ChunkBuffer()

	if shuffle:
		import random
		random.shuffle(calls)

	for event, data in calls:
		if event == 'rpc_result':
			return data
		result = buf.receive(data)
		if result is not None:
			return result

	return None  # not all chunks received yet


# --- sio_send: small messages ---

def test_send_small_uses_plain_event():
	calls, emit = make_emit_recorder()
	sio_send(emit, 'rpc_result', 'id1|hello')
	assert len(calls) == 1
	assert calls[0] == ('rpc_result', 'id1|hello')

def test_send_small_does_not_use_chunk_event():
	calls, emit = make_emit_recorder()
	sio_send(emit, 'rpc_result', 'id1|hello')
	assert all(event != 'rpc_result_chunk' for event, _ in calls)

def test_send_exactly_one_byte_below_chunk_size():
	calls, emit = make_emit_recorder()
	message = 'id1|' + 'x' * (CHUNK_SIZE - len('id1|') - 1)
	sio_send(emit, 'rpc_result', message)
	assert len(calls) == 1
	assert calls[0][0] == 'rpc_result'


# --- sio_send: large messages ---

def test_send_large_uses_chunk_event():
	calls, emit = make_emit_recorder()
	message = 'id1|' + 'x' * CHUNK_SIZE
	sio_send(emit, 'rpc_result', message)
	assert all(event == 'rpc_result_chunk' for event, _ in calls)

def test_send_large_correct_number_of_chunks():
	calls, emit = make_emit_recorder()
	payload = 'x' * (CHUNK_SIZE * 2 + 1)
	sio_send(emit, 'rpc_result', f'id1|{payload}')
	assert len(calls) == 3

def test_send_chunk_event_name_is_event_plus_chunk_suffix():
	calls, emit = make_emit_recorder()
	sio_send(emit, 'rpc_request', 'id1|' + 'x' * CHUNK_SIZE)
	assert all(event == 'rpc_request_chunk' for event, _ in calls)

def test_send_chunk_envelope_format():
	calls, emit = make_emit_recorder()
	payload = 'x' * CHUNK_SIZE
	sio_send(emit, 'rpc_result', f'id1|{payload}')
	_, data = calls[0]
	chunk_num, num_chunks, call_ID, _ = data.split('|', 3)
	assert chunk_num == '0'
	assert call_ID == 'id1'
	assert int(num_chunks) > 0

def test_send_chunk_numbers_are_sequential():
	calls, emit = make_emit_recorder()
	sio_send(emit, 'rpc_result', 'id1|' + 'x' * (CHUNK_SIZE * 3))
	chunk_nums = [int(data.split('|', 1)[0]) for _, data in calls]
	assert chunk_nums == list(range(len(calls)))


# --- ChunkBuffer ---

def test_buffer_returns_none_before_all_chunks_arrive():
	buf = ChunkBuffer()
	# send first of two chunks
	result = buf.receive(f'0|2|id1|first_half')
	assert result is None

def test_buffer_returns_assembled_when_all_chunks_arrive():
	buf = ChunkBuffer()
	buf.receive('0|2|id1|hello_')
	result = buf.receive('1|2|id1|world')
	assert result == 'hello_world'

def test_buffer_reassembles_out_of_order_chunks():
	buf = ChunkBuffer()
	buf.receive('1|2|id1|world')
	result = buf.receive('0|2|id1|hello_')
	assert result == 'hello_world'

def test_buffer_clears_state_after_completion():
	buf = ChunkBuffer()
	buf.receive('0|2|id1|hello_')
	buf.receive('1|2|id1|world')
	assert 'id1' not in buf._buffers

def test_buffer_handles_concurrent_call_ids():
	buf = ChunkBuffer()
	buf.receive('0|2|id1|a')
	buf.receive('0|2|id2|x')
	result1 = buf.receive('1|2|id1|b')
	result2 = buf.receive('1|2|id2|y')
	assert result1 == 'ab'
	assert result2 == 'xy'


# --- round-trip ---

def test_roundtrip_small_message():
	message = 'id1|/endpoint|{"key": "value"}'
	assert send_via_buffer(message) == message

def test_roundtrip_large_message():
	payload = 'x' * (CHUNK_SIZE * 2 + 500)
	message = f'id1|{payload}'
	assert send_via_buffer(message) == message

def test_roundtrip_message_containing_pipe_characters():
	message = 'id1|/endpoint|{"key": "val|ue|with|pipes"}'
	assert send_via_buffer(message) == message

def test_roundtrip_out_of_order_chunks():
	payload = 'x' * (CHUNK_SIZE * 3)
	message = f'id1|{payload}'
	assert send_via_buffer(message, shuffle=True) == message
