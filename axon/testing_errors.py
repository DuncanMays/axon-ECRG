import sys
import traceback

from errors import AxonError
from concurrent.futures import ThreadPoolExecutor

# this function checks if an error flag has been set and raises the corresponding error if it has
def error_handler(return_obj):
	if (return_obj['errcode'] == 1):
		# an error occured in worker, raise it
		(error_info, error) = return_obj['result']

		print('the following error occured in worker:')
		print(error_info)
		raise(error)

	else:
		# returns the result
		return return_obj['result']

def target_fn():
	print('hello!')
	# raise BaseException('noooo!!!')
	raise AxonError('axon is broke :(')
	return True

def test_error_handler():

	return_object = {
		'errcode': 0,
		'result': None,
	}

	try:

		return_object['result'] = target_fn()

	except:
		return_object['errcode'] = 1
		return_object['result'] = (traceback.format_exc(), sys.exc_info()[1])

	result = None

	try:
		result = error_handler(return_object)
	except(AxonError):
		print('an axon error occured')

	print(result)

def test_executor_errors():

	e = ThreadPoolExecutor(max_workers=10)

	f = e.submit(target_fn)

	try:
		result = f.result()
	except(AxonError):
		print('an axon error occured')

# test_error_handler()
test_executor_errors()