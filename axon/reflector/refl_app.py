import axon
import time
import threading
import socketio
import logging

from concurrent.futures import ThreadPoolExecutor
from flask import Flask

from axon.config import transport
from axon.HTTP_transport.config import port as default_http_port
from axon.reflector import config as refl_config
from axon.reflector.config import passthrough_serialize, passthrough_deserialize
from axon.reflector.CloudClient import CloudClientNamespace
from axon.reflector.CloudWorker import CloudWorkerNamespace


def init_logger():

	logger = logging.getLogger(__name__)
	logger.setLevel(logging.DEBUG)

	c_handler = logging.StreamHandler()
	f_handler = logging.FileHandler(refl_config.log_file)

	log_format = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
	c_handler.setFormatter(log_format)
	f_handler.setFormatter(log_format)

	logger.addHandler(c_handler)
	logger.addHandler(f_handler)

	return logger


def run(endpoint='reflected_services', ws_port=5000, http_port=default_http_port):

	logger = init_logger()

	http_tl = transport.worker(http_port)
	tpe = ThreadPoolExecutor(axon.config.NUM_OPEN_REQS)

	http_tl.serialize = passthrough_serialize
	http_tl.deserialize = passthrough_deserialize

	http_thread = threading.Thread(target=http_tl.run, daemon=True)
	http_thread.start()
	time.sleep(0.5)

	http_node = axon.worker.ServiceNode({}, endpoint, tl=http_tl, executor=tpe)

	sio = socketio.Server(async_mode='threading')
	sio.register_namespace(CloudClientNamespace(http_node, logger))
	sio.register_namespace(CloudWorkerNamespace(http_node, logger))

	logger.debug('Reflector start')

	app = Flask(__name__)
	app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)
	app.run(host='0.0.0.0', port=ws_port)
