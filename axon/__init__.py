import axon.client
import axon.worker
import axon.utils
import axon.config

import axon.notice_board_app

def start_notice_board():
	print('starting notice board app')
	notice_board_app.app.run(host='0.0.0.0', port=config.comms_config.notice_board_port)

