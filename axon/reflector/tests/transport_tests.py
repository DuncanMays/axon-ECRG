import pytest
import axon
import socketio
import random

from axon.reflector.tests.ITL_test import refl_thread, DummyClass, echo_worker

def test_basic(echo_worker):
	url = f'http://localhost:5000/reflected_services'
	sio = socketio.Client()
	sio.connect(url)
	itl_client = axon.reflector.EdgeClient(sio)

	stub = axon.client.get_stub(url, tl=itl_client)

	msg_size = 1_000
	msg = ''.join([str(random.randint(0,9)) for i in range(msg_size)])

	response = stub.echo_worker.rpc.echo(msg).join()
	
	assert response == msg

# def test_big(echo_worker):
# 	url = f'http://localhost:5000/reflected_services'
# 	sio = socketio.Client()
# 	sio.connect(url)
# 	itl_client = axon.reflector.EdgeClient(sio)

# 	stub = axon.client.get_stub(url, tl=itl_client)

# 	msg_size = 1_000_000
# 	msg = ''.join([str(random.randint(0,9)) for i in range(msg_size)])

# 	response = stub.echo_worker.rpc.echo(msg).join()
	
# 	assert response == msg

