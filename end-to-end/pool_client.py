import sys
sys.path.append('..')
import axon

stub = axon.client.get_RemoteWorker('localhost')

stub.rpcs.print_this('Hi there!').join()
stub.rpcs.print_this('Hi there!').join()

