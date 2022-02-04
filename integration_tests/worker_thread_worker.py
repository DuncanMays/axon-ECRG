import sys
sys.path.append('..')
from axon import worker, client

print(dir(axon))

@worker.rpc()
async def self_log(ip_addr):
	print('self_log called from:', ip_addr)
	log_stub = client.get_simplex_rpc_stub(ip_addr, msg='log')
	await log_stub('hello world')

worker.init()