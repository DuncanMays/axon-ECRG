import sys
sys.path.append('..')

import axon

from math import ceil

from concurrent.futures import Future

from axon.transport_client import req_executor, error_handler, AsyncResultHandle, AbstractTransportClient
from axon.utils import get_ID_generator

class EdgeClient(AbstractTransportClient):

	def __init__(self, sio):
		super().__init__()
		
		self.sio = sio
		self.pending_reqs = {}
		self.chunk_buffers = {}
		self.call_ID_gen = get_ID_generator()

		self.sio.emit('client_header')

		@self.sio.event
		def rpc_result(return_str):
			call_ID, result_str = return_str.split('|', 1)
			# logger.debug('RPC response for call_ID: %s', call_ID)
			result_future = self.pending_reqs[call_ID]
			result_future.set_result(result_str)

		@self.sio.event
		def rpc_result_chunk(event_str):
			chunk_num, num_chunks, call_ID, chunk_str = event_str.split('|', 3)
			# logger.debug('RPC response chunk %s for call_ID: %s', chunk_num, call_ID)

			chunk_obj = {
				'chunk_str': chunk_str,
				'chunk_num': int(chunk_num)
			}

			if (call_ID in self.chunk_buffers):
				self.chunk_buffers[call_ID].append(chunk_obj)

			else :
				self.chunk_buffers[call_ID] = [chunk_obj]

			if (len(self.chunk_buffers[call_ID]) == int(num_chunks)):

				chunks = self.chunk_buffers[call_ID]
				chunks.sort(key=lambda x: x['chunk_num'])
				chunk_strs = [b['chunk_str'] for b in chunks]
				result_str = ''.join(chunk_strs)

				result_future = self.pending_reqs[call_ID]
				result_future.set_result(result_str)

				# logger.debug('recieved all chunks for call_ID: %s', call_ID)
				del self.chunk_buffers[call_ID]

		@self.sio.event
		def disconnect():
			self.disconnect_handler()

	def get_config(self):
		# the ITL client sends requests through an already established socket connection, so config info like the port number and scheme don't exist
		return None

	def net_call(self, url, param_str):

		url_components = url.split('/')
		url_head = '/'.join(url_components[:3])
		endpoint = '/' + '/'.join(url_components[3:])

		call_ID = next(self.call_ID_gen)
		result_future = Future()
		self.pending_reqs[call_ID] = result_future

		# logger.debug('RPC call to: %s for: %s call_ID: %s', endpoint, call_ID)

		chunk_size = 100_000

		req_str = f'{call_ID}|{endpoint}|{param_str}'

		if (len(req_str) < chunk_size):
			self.sio.emit('rpc_request', data=req_str)

		else:
			num_chunks = ceil(len(req_str)/chunk_size)

			for i in range(num_chunks):
				chunk_str = req_str[ chunk_size*i : chunk_size*(i+1) ]
				self.sio.emit('rpc_request_chunk', data=f'{str(i)}|{str(num_chunks)}|{call_ID}|{chunk_str}')		
		
		return result_future.result()

	def disconnect_handler(self):

		# send a worker disconnect error back through each pending request
		for call_ID in self.pending_reqs:
			result_str = serialize(BaseException('WorkerDisconnect'))
			result_str = f'1|{result_str}'
			self.pending_reqs[call_ID].set_result(result_str)