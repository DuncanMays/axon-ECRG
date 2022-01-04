import sys
sys.path.append('..')

import axon

nb = axon.discovery.NoticeBoard()

@nb.app.route('/discovery')
def fn():
	return 'great success'

nb.start()
