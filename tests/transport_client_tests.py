from sys import path
path.append('..')

import threading
import axon

client = axon.transport_client

config = {
	'name': 'fn',
	'endpoint_prefix': '/'
}

# url = 'http://'+str(self.remote_ip)+':'+str(comms_config.worker_port)+'/'+self.endpoint_prefix+self.__name__

url = 'http://localhost:8000/'+config['endpoint_prefix']+config['name']

# a = client.call_rpc(url, (1, ), {'one': 1})

# print(a.join())
