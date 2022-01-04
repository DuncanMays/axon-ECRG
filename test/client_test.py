# import sys
# sys.path.append('..')

# from axon.client import RemoteWorker, start_client
# from axon.utils import get_active_workers

# import asyncio

# async def main():

# 	# print('starting client')
# 	# await start_client()

# 	print('getting worker ips')
# 	worker = RemoteWorker('localhost')

# 	num_processes = 60

# 	print('doing work')
# 	result_futures = [worker.rpcs.do_work(3) for i in range(num_processes)]
	
# 	print('awaiting responses')
# 	results = await asyncio.gather(*result_futures)

# 	print('responses recieved:')
# 	print(results)

# if (__name__ == '__main__'):
# 	asyncio.run(main())

import sys
sys.path.append('..')
import axon

import asyncio
import aiohttp

async def main():
	print('broadcasting')

	print(await axon.discovery.broadcast(single_host=False, timeout=3))
		
	print('all done')

asyncio.run(main())