from .config import comms_config
from .utils import serialize, deserialize

from flask import Flask
from flask import request as route_req

# this class is a notice board, which workers can sign into and out of to notify other workers of their presence
class NoticeBoard():

	def __init__(self, name='notice board', port=comms_config.notice_board_port):

		self.ip_set = set({})
		self.app = Flask(name)
		self.port = port

		# we now add routes to the app

		@self.app.route('/sign_in', methods=['GET'])
		def sign_in():
			remote_addr = route_req.remote_addr
			self.ip_set.add(remote_addr)

			print('/sign_in: ip address:', remote_addr, 'recorded, now have', len(self.ip_set), 'registered addresses')

			return 'sign in successful'

		@self.app.route('/sign_out', methods=['GET'])
		def sign_out():
			remote_addr = route_req.remote_addr

			try:
				self.ip_set.remove(remote_addr)
				print('/sign_out: ip address:', remote_addr, 'removed, now have', len(self.ip_set), 'registered addresses')
				return 'sign out successful'

			except(KeyError):
				print('/sign_out: ip address:', remote_addr, 'not recorded')
				return 'ip address not recorded'


		@self.app.route('/get_ips', methods=['GET'])
		def get_ips():
			self.ip_list = list(self.ip_set)
			return serialize(self.ip_list)

		# route to shut the server down
		@self.app.route('/kill')
		def kill():
			func = route_req.environ.get('werkzeug.server.shutdown')

			if func is None:
				raise RuntimeError('Not running with the Werkzeug Server')

			func()
			return 'shutting down'

	def get_ips(self):
		return list(self.ip_set)

	def start(self):
		print('starting notice board app')
		self.app.run(host='0.0.0.0', port=self.port)