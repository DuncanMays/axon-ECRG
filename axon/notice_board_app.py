from .config import comms_config
from .utils import serialize, deserialize

from flask import Flask
from flask import request as route_req

# this class is a notice board, which workers can sign into and out of to notify other workers of their presence
class NoticeBoard():

	def __init__(self, name='notice board', port=comms_config.notice_board_port, show_logs=True):

		self.ip_set = set({})
		self.app = Flask(name)
		self.port = port
		self.show_logs = show_logs

		# we now add routes to the app

		@self.app.route('/sign_in', methods=['GET'])
		def sign_in():
			remote_addr = route_req.remote_addr
			self.ip_set.add(remote_addr)

			self.log('/sign_in: ip address:', remote_addr, 'recorded, now have', len(self.ip_set), 'registered addresses')

			return 'sign in successful'

		@self.app.route('/sign_out', methods=['GET'])
		def sign_out():
			remote_addr = route_req.remote_addr

			try:
				self.ip_set.remove(remote_addr)
				self.log('/sign_out: ip address:', remote_addr, 'removed, now have', len(self.ip_set), 'registered addresses')
				return 'sign out successful'

			except(KeyError):
				self.log('/sign_out: ip address:', remote_addr, 'not recorded')
				return 'ip address not recorded'


		@self.app.route('/get_ips', methods=['GET'])
		def get_ips():
			self.ip_list = list(self.ip_set)
			return serialize(self.ip_list)

		# route to shut the server down in case sigint fails
		@self.app.route('/kill')
		def kill():
			func = route_req.environ.get('werkzeug.server.shutdown')

			if func is None:
				raise RuntimeError('Not running with the Werkzeug Server')

			func()
			return 'shutting down'

		# a default route to provide basic info about the axon node, namely, that it's a notice board
		@self.app.route('/_type', methods=['GET'])
		def _type():
			return 'notice_board'

	def get_ips(self):
		return list(self.ip_set)

	def start(self):
		self.log('starting notice board app')
		self.app.run(host='0.0.0.0', port=self.port)

	def log(self, *args):
		if self.show_logs: print(*args)