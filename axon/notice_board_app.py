from .config import comms_config
from .utils import serialize, deserialize

from flask import Flask
from flask import request as route_req
import pickle

ip_set = set({})
app = Flask(__name__)

@app.route('/sign_in', methods=['GET'])
def sing_in():
	remote_addr = route_req.remote_addr
	ip_set.add(remote_addr)

	print('/sign_in: ip address:', remote_addr, 'recorded, now have', len(ip_set), 'registered addresses')

	return 'sign in successful'

@app.route('/sign_out', methods=['GET'])
def sign_out():
	remote_addr = route_req.remote_addr

	try:
		ip_set.remove(remote_addr)
		print('/sign_out: ip address:', remote_addr, 'removed, now have', len(ip_set), 'registered addresses')
		return 'sign out successful'

	except(KeyError):
		print('/sign_out: ip address:', remote_addr, 'not recorded')
		return 'ip address not recorded'


@app.route('/get_ips', methods=['GET'])
def get_ips():
	ip_list = list(ip_set)
	return serialize(ip_list)

if (__name__ == '__main__'):
	print('starting notice board app')
	app.run(host='0.0.0.0', port=comms_config.notice_board_port)