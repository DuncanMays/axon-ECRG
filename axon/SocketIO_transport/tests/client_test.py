import sys
sys.path.append('..')

import socketio
import time
import pytest
import axon.SocketIO_transport.client as client


def test_client():

	c = client.SocketIOTransportClient()
	r = c.call_rpc('http://localhost:5050/endpoint', (5, ), {})
	print(r)