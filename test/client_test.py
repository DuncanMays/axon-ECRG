import sys
sys.path.append('..')

from axon.client import RemoteWorker, start_client
from axon.utils import get_active_workers
from axon.discovery import broadcast_discovery, get_ips
from axon.config import comms_config
import asyncio

async def main():

	worker = RemoteWorker('127.0.0.1')

	num_processes = 6

	print('starting client')
	await start_client()

	print('doing work')
	result_futures = [worker.rpcs.do_work('3', msg='all done!') for i in range(num_processes)]
	
	print('awaiting responses')
	results = await asyncio.gather(*result_futures)

	print('responses recieved:')
	print(results)

if (__name__ == '__main__'):
	asyncio.run(main())