from .utils import serialize, deserialize, get_open_port
from .config import comms_config

from flask import Flask
from flask import request as route_req
from threading import Thread, Lock
import sys
import uuid
import time
import requests
import asyncio

# stops flask from outputting starting message
cli = sys.modules['flask.cli']
cli.show_server_banner = lambda *x: 'hello there'

# stops flask from printing to console when it fulfills a request
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
log.disabled = True

# this class works the same way as asyncio events, except it cannot be cleared
# the important difference is that the arguements(s) given to set will be returned by wait
class ReturnEvent():

	def __init__(self):
		self.event = asyncio.Event()
		self.value = None

	async def get_return_value(self):
		await self.event.wait()
		return self.value

	def put_return_value(self, value):
		self.value = value
		self.event.set()

# this class encapsulates an app that will listen for incoming result requests from duplex RPCs
class RVL():

	def __init__(self, event_loop):
		self.app = Flask(__name__)
		self.event_loop = event_loop
		self.stubs = {}
		self.port = None
		self.running = False

		# adds a route that will listen for incoming result requests from duplex RPCs
		def lookup():

			(uuid, result_obj) = deserialize(route_req.form['msg'])

			return_event = self.stubs[uuid]

			# callback = lambda : return_event.put_return_value(result_obj)
			def callback():
				return_event.put_return_value(result_obj)
				del self.stubs[uuid]


			self.event_loop.call_soon_threadsafe(callback)

			return 'great sucess'

		self.app.route("/_return_value_linker", methods=['POST'])(lookup)

	def register(self, uuid, event):
		self.stubs[uuid] = event

	def start(self):

		def start_app(port):
			self.app.run(host='0.0.0.0', port=port)

		# finds an available port
		rvl_port = get_open_port(lower_bound=comms_config.RVL_port)
		self.port = rvl_port

		# starts a thread that the app will run in
		self.app_thread = Thread(target=start_app, args=(rvl_port,))
		self.app_thread.daemon = True
		self.app_thread.start()

		# we now poll the rvl app until it starts responding to tell when it has started. We don't want the function to complete without anything listenning for incoming results

		# registers a return event
		call_id = uuid.uuid4()
		return_event = ReturnEvent()
		self.register(call_id, return_event)

		# polls every 0.1 seconds until we can set the event
		while True:
			time.sleep(0.1)

			try:
				url = 'http://localhost:'+str(rvl_port)+'/_return_value_linker'
				data = {'msg': serialize((call_id, ''))}

				# if the rvl port isn't open, this should throw
				requests.post(url=url, data=data)

				# if PC gets here, the RVL port is open, can stop polling
				break

			except(requests.exceptions.ConnectionError):
				pass

		self.running = True