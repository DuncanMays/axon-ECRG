import time
from threading import Thread

import sys
sys.path.append('..')
# sys.path.append('./')
import axon

# the notice board will be run in a separate thread so we can run a client in the main thread to test it
nb = axon.discovery.NoticeBoard()
nb_thread = Thread(target=nb.start)
nb_thread.daemon = True

def test_sign_in_sign_out():
	print('test_sign_in_sign_out')

	# start the notice board thread and waits a little bit for it to startup
	nb_thread.start()

	time.sleep(0.5)

	# signs into a notice board and confirms
	axon.discovery.sign_in(ip='localhost')
	ips = axon.discovery.get_ips(ip='localhost')

	if '127.0.0.1' in ips:
		print('sign in worked!')

	elif'127.0.0.1' not in ips:
		raise(BaseException('sign in didn\'t work!'))

	axon.discovery.sign_out(ip='localhost')
	ips = axon.discovery.get_ips(ip='localhost')

	if '127.0.0.1' in ips:
		raise(BaseException('sign out didn\'t work!'))

	elif'127.0.0.1' not in ips:
		print('sign out worked!')