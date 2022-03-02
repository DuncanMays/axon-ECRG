from .config import comms_config

import pickle
import requests
import aiohttp
import asyncio
import codecs
import time
import socket
import copy

def GET(url, timeout=comms_config.request_timeout):
	resp = requests.get(url, timeout=timeout)
	return resp.status_code, resp.text

async def async_GET(url, timeout=comms_config.request_timeout):
	async with aiohttp.ClientSession(conn_timeout=timeout) as session:
		async with session.get(url) as resp:
			return resp.status, await resp.text()

def POST(url, data=None, timeout=comms_config.request_timeout):
	resp = requests.post(url=url, data=data, timeout=timeout)
	return resp.status_code, resp.text

async def async_POST(url, data=None, timeout=comms_config.request_timeout):
	async with aiohttp.ClientSession(conn_timeout=timeout) as session:
		async with session.post(url, data=data) as resp:
			return resp.status, await resp.text()

# pickle operates on bytes, but http operates on strings, so we've gotta convert pickles to and from a string
def serialize(obj):
	pickled = pickle.dumps(obj)
	return codecs.encode(pickled, "base64").decode()

# pickle operates on bytes, but http operates on strings, so we've gotta convert pickles to and from a string
def deserialize(obj_str):
	obj_bytes = codecs.decode(obj_str.encode(), "base64")
	return pickle.loads(obj_bytes)

def get_active_workers():
	status, text = GET('http://'+str(comms_config.notice_board_ip)+':'+str(comms_config.notice_board_port)+'/get_ips')

	if (status == 404): print('notice board not found')

	return deserialize(text)

self_ip = None
def get_self_ip():
	global self_ip

	if (self_ip == None):
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(("8.8.8.8", 80))
		ip = s.getsockname()[0]
		s.close()

		self_ip = ip

		return ip

	else:
		return self_ip

# scans for an available port in between upper_bound and lower_bound
def get_open_port(lower_bound=8000, upper_bound=9000):

	for target_port in range(lower_bound, upper_bound):
		# defines a socket, AF_INIT means ipv4 and SOCK_STREAM means TCP
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		location = ("127.0.0.1", target_port)
		# will return 0 if the port is available
		result = sock.connect_ex(location)

		if result != 0:
			sock.close()
			return target_port

	sock.close()
	raise BaseException('No available ports in between '+str(lower_bound)+' and '+str(upper_bound))

	# accepts two dicts, target and source
# in any shared keys between the two will be overwritten to source's value, and any keys in source will be copied to target, with thei values
def overwrite(target, source):
	# to avoid aliasing
	target = copy.copy(target)

	for key in source:
		target[key] = source[key]

	return target