import sys
sys.path.append('..')

import asyncio
import axon

hello_world = axon.simplex_stubs.SyncSimplexStub(worker_ip='localhost', rpc_name='hello_world')

result = hello_world()

print(result)