import sys
sys.path.append('..')
import axon

stub = axon.client.get_RemoteWorker('localhost')

num_calls = 10
call_handles = [stub.rpcs.print_this(i) for i in range(num_calls)]
results = [c.join() for c in call_handles]