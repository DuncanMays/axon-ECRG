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
# the important difference is that the arguements(s) given to set will be returned by await
class ReturnEvent_coro():

	def __init__(self):
		self.event = asyncio.Event()
		self.value = None
		self.event_loop = None

	async def init(self, loop=None):
		if loop == None:
			self.event_loop = asyncio.get_running_loop()
		else:
			self.event_loop = loop

	async def get_return_value(self):
		await self.event.wait()
		return self.value

	def put_return_value(self, value):

		# checks that the event loop exists and is running
		if self.event_loop == None:
			print('call ID:', uuid)
			raise(BaseException('ReturnEvent_coro not initialized with event loop'))
		elif not self.event_loop.is_running():
			print('call ID:', uuid)
			raise(BaseException('ReturnEvent_coro has inactive event loop'))

		# schedules a callback on the event loop that initialized this ReturnEvent_coro to set the return value

		def callback():
			self.value = value
			self.event.set()

		self.event_loop.call_soon_threadsafe(callback)

class ReturnEvent_async():

	def __init__(self):
		self.lock = Lock()
		self.lock.acquire()
		self.value = None

	# this function is called from a separate thread that wishes to get the value
	def get_return_value(self):
		self.lock.acquire()
		return self.value

	def put_return_value(self, value):
		
		self.value = value
		self.lock.release()

# this class encapsulates an app that will listen for incoming result requests from duplex RPCs
class RVL():

	def __init__(self):
		# the app that will run in a separate thread and listen for incomming result requests
		self.app = Flask(__name__)
		# boolean indiating weathre or not the app thread is running
		self.running = False
		# where asyncio events and such will be posted
		self.event_loop = None

		self.stubs = {}
		self.port = None

		# adds a route that will listen for incoming result requests from duplex RPCs
		def lookup():

			# the ID and result of the function call
			serialized_result = route_req.form['result']
			uuid = deserialize(route_req.form['id'])
			# gets the return event, with which we may pass the return value to the caller of the function
			return_event = self.stubs[uuid]
			# passes the return value back to the caller of the RPC
			return_event.put_return_value(serialized_result)
			# clears the record of the RPC call to prevent memory leak
			del self.stubs[uuid]

			return 'result returned successfully'

		self.app.route("/_return_value_linker", methods=['POST'])(lookup)

	def register(self, uuid, event):
		self.stubs[uuid] = event

	def start_app(self):

		def app_fn(port):
			self.app.run(host='0.0.0.0', port=port, threaded=False)

		# finds an available port
		rvl_port = get_open_port(lower_bound=comms_config.RVL_port)
		self.port = rvl_port
		# starts a thread that the app will run in
		self.app_thread = Thread(target=app_fn, args=(rvl_port,), name='rvl_thread')
		self.app_thread.daemon = True
		self.app_thread.start()

		# we now poll the rvl app until it starts responding to tell when it has started. We don't want the function to complete without anything listenning for incoming results

		# registers a return event
		call_id = uuid.uuid4()
		return_event = ReturnEvent_async()
		self.register(call_id, return_event)

		# this has to be done before this function completes or lookup will raise an exception
		self.running = True

		# polls every 0.1 seconds until we can set the event
		while True:
			time.sleep(0.1)

			try:
				url = 'http://localhost:'+str(rvl_port)+'/_return_value_linker'
				data = {'msg': serialize((call_id, 'init return val'))}

				# if the rvl port isn't open, this should throw
				requests.post(url=url, data=data)

				# if PC gets here, the RVL port is open, can stop polling
				break

			except(requests.exceptions.ConnectionError):
				pass
