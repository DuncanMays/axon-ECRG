import sys
sys.path.append('..')

from axon.client import RemoteWorker, start_client
from axon.utils import get_active_workers
from axon.discovery import broadcast_discovery, get_ips
import asyncio

async def main():

	# finding notice board
	nb_ip = await broadcast_discovery(endpoint='/discovery', num_hosts=1)

	worker_ips = get_ips(nb_ip.pop())

	# print('getting worker ips')
	worker = RemoteWorker(worker_ips.pop())

	num_processes = 6

	print('starting client')
	await start_client()

	print('doing work')
	result_futures = [worker.rpcs.do_work(3, msg='all done!') for i in range(num_processes)]
	
	print('awaiting responses')
	results = await asyncio.gather(*result_futures)

	print('responses recieved:')
	print(results)

if (__name__ == '__main__'):
	asyncio.run(main())