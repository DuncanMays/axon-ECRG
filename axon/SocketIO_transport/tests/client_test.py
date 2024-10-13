import sys
sys.path.append('..')

import socketio
import time
import pytest
import axon.SocketIO_transport.client as client
import random


def test_client():

	c = client()
	r = c.call_rpc('http://localhost:5050/print_x', (5, ), {})
	print(r)

def test_big_message():

	msg_size = 500_000
	msg = ''.join([str(random.randint(0,9)) for i in range(msg_size)])

	c = client()
	r = c.call_rpc('http://localhost:5050/big_input', (msg, ), {})
	print(r)