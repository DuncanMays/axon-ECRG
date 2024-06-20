import sys
sys.path.append('..')

import axon
import asyncio

async def main():

	s = axon.client.get_ServiceStub('localhost', stub_type=axon.stubs.SyncStub)
	
	print(dir(s))
	print(dir(s.list_service))

	s = axon.client.get_ServiceStub('localhost/list_service', stub_type=axon.stubs.SyncStub)
	
	print(dir(s))

	# print(s.list_service[1])
	# print(s.rpc.do_work(1))
	# print(s.rpc.print_msg('hello!'))

	# r = axon.client.get_ServiceStub('localhost/rpc', stub_type=axon.stubs.SyncStub)
	# print(r.do_work(1))
	# print(r.print_msg('hello!'))

	# l = axon.client.get_ServiceStub('localhost/list_service', stub_type=axon.stubs.SyncStub)
	# print(l[1])

	# rw = axon.client.get_RemoteWorker('http://localhost:8000')
	# print(await rw.list_service[1])
	# print(await rw.rpcs.do_work(1))
	# print(await rw.rpcs.print_msg('hello!'))

	
if (__name__ == '__main__'):
	asyncio.run(main())