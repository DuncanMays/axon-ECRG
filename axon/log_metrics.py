import psutil
import logging
import os

if (__name__ == '__main__'):
	logger = logging.getLogger(__name__)
	logger.setLevel(logging.INFO)
	handler = logging.FileHandler('./reflector.metrics')
	log_format = logging.Formatter('%(asctime)s | %(message)s')
	handler.setFormatter(log_format)
	logger.addHandler(handler)

	cpu = psutil.cpu_percent()
	ram = psutil.virtual_memory().percent
	net = psutil.net_io_counters()

	logger.info('CPU %s RAM %s bytes_sent %s bytes_recv %s', cpu, ram, net.bytes_sent, net.bytes_recv)