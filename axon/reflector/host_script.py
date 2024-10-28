import sys
sys.path.append('..')

import axon
import cloudpickle

itlw = axon.reflector.ITLW(url='143.198.32.69', name='host_worker')

@axon.worker.rpc(tl=itlw)
# @axon.worker.rpc()
def host(service_str, name):

	service = cloudpickle.loads(service_str)
	axon.worker.register_ServiceNode(service, name)
	itlw.update_profile()
	return 'success'

axon.worker.init()