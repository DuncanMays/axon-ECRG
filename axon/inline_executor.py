from concurrent.futures import Future, Executor

class InlineExecutor(Executor):

	def submit(self, target, *args, **kwargs):
		result_future = Future()

		kwargs['in_parallel'] = False

		result_future.set_result(target(*args, **kwargs))
		return result_future
