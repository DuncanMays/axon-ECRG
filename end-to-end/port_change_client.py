import sys
sys.path.append('..')
import axon

stub = axon.client.get_RemoteWorker('localhost', 5000)

stub.rpcs.print_str('hello!').join()
stub.test.hello().join()