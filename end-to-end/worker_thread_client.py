import sys
sys.path.append('..')
import axon
import asyncio
from threading import Thread

# defining the logging RPC
@axon.worker.rpc()
def log(msg):
	print(msg)

# defines a thread to run the worker separately from the rest of the script
worker_thread = Thread(target=axon.worker.init)

async def main():
	# finds the ip address of the worker
	[remote_ip] = await axon.discovery.broadcast_discovery(num_hosts=1)

	# we have to start the local worker thread after running broadcast_discovery or it will detect the local worker instead of the remote one
	worker_thread.start()

	# defines client stub
	worker = axon.client.RemoteWorker(remote_ip)

	# calls RPC on worker that itself calls the RPC defined above
	await worker.rpcs.self_log(axon.utils.get_self_ip(), 'from client')

asyncio.run(main())