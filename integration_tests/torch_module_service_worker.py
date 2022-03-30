import sys
sys.path.append('..')

import axon
import torch

tensor = torch.randn([2,2])

if (__name__ == '__main__'):

	axon.worker.ServiceNode(tensor, 'tensor_service')

	print('initializing worker')
	axon.worker.init()