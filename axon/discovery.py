from .utils import GET, POST
from .config import comms_config
from .utils import serialize, deserialize, get_self_ip
from .notice_board_app import NoticeBoard

from flask import Flask
from flask import request as route_req
import requests, aiohttp
import asyncio 

# broadcasts to all IPs on the LAN, and returns a list of the IPs that provide a response
async def broadcast(endpoint='discovery', port=comms_config.notice_board_port, single_host=True, timeout=10):
	self_ip = get_self_ip()
	# the first three numbers of the ip address, representing the LAN address
	base_addr = '.'.join(self_ip.split('.')[:-1])+'.'
	# the urls we will be sending requests to
	host_ips = range(0, 255)

	# the future that holds all the request coroutines
	all_reqs = None
	# where the IP address of the first discovered endpoint will be stored
	result_holder = {'result': []}

	# we need to create a clientsession to send async requests
	async with aiohttp.ClientSession(conn_timeout=timeout) as session:

		# coroutine that we will call on each ip in host_ips
		async def req_fn(ip, result_holder):
			url = 'http://'+base_addr+str(ip)+':'+str(port)+'/'+endpoint
			status = None
			test = None

			# catches no connection and timeout errors
			try:
				# sends request and awaits result
				async with session.get(url) as resp:
					status = resp.status
					test = await resp.text()

				# if there is a worker at ip, set the result
				result_holder['result'].append(base_addr+str(ip))

				# if we are to stop after one response, cancel the other coroutines
				if (single_host):
					all_reqs.cancel()

				return

			except(aiohttp.client_exceptions.ClientConnectorError):
				return

			except(aiohttp.client_exceptions.ServerTimeoutError):
				return


		# the futures returned by sending requests to each host
		futures = [req_fn(ip, result_holder) for ip in host_ips]
		all_reqs = asyncio.gather(*futures)

		try:	
			await all_reqs

		except(asyncio.exceptions.CancelledError):
			pass

	if (single_host):
		return result_holder['result'][0]

	else:
		return result_holder['result']

def sign_in(ip='localhost', port=comms_config.notice_board_port):
	try:
		status, text = GET('http://'+str(ip)+':'+str(port)+'/sign_in')

		if (hash(text) != hash('sign in successful')):
			print('sign_in: notice board gave warning, may not be registered')

	except(requests.exceptions.ConnectionError):
		print('sign in: no notice board found at '+str(comms_config.notice_board_ip))

def sign_out(ip='localhost', port=comms_config.notice_board_port):
	try:
		status, text = GET('http://'+str(ip)+':'+str(port)+'/sign_out')

		if (hash(text) == hash('ip address not recorded')):
			print('sing_out: not registered at given ip')

		elif (hash(text) != hash('sign out successful')):
			print('sing_out: notice board gave warning')

	except(requests.exceptions.ConnectionError):
		print('sign out: no notice board found at '+str(comms_config.notice_board_ip))