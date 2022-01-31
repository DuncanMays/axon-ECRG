import sys
sys.path.append('../axon')
from inline_executor import InlineExecutor

def duplex_wrapper(fn, executor):
	print(executor.__class__)

	def wrapped_fn():
		print(executor.__class__ == InlineExecutor)

		# this function will run in a separate thread, will execute the RPC and return the result with a POST request
		def wrk_fn(fn, params_str, calling_ip):
			print(executor.__class__ == InlineExecutor)

			# deserializes parameters
			(call_info, args, kwargs) = deserialize(params_str)

			# the info needed to return the result
			call_id = call_info['id']
			rvl_port = call_info['rvl_port']

			# if fn is a coroutine, it needs to be run with an event loop
			if inspect.iscoroutinefunction(fn): fn = async_wrapper(fn)

			# catches and returns any error
			fn = error_wrapper(fn)

			# runs the function
			return_object = fn(args, kwargs)

			# returns the result via a POST request
			url = 'http://'+calling_ip+':'+str(rvl_port)+'/_return_value_linker'
			data = {'msg': serialize((call_id, return_object))}
			requests.post(url=url, data=data)

		print(executor.__class__ == InlineExecutor)
		print(isinstance(executor, InlineExecutor))

		if isinstance(executor, InlineExecutor):
			print('fuck')

		# because flask, and WSGI servers in general, cannot schedule code to execute after a route completes, inline duplex RPCs would have to send the returning request before the calling request completes
		# to prevent this, we must run the RPC in a separate thread, to preserve synchronous semantics, we must use a threadlock with other inline RPCs
		if isinstance(executor, InlineExecutor):

			# ensures the inline lock is acquired and released
			def wrapped_fn(fn, params_str, calling_ip):
				with inline_lock:
					result = wrk_fn(fn, params_str, calling_ip)

				return result

			wrk_fn = wrapped_fn
			# executor = Thread

		# params_str = route_req.form['msg']
		# calling_ip = route_req.remote_addr

		print(executor.__class__ == InlineExecutor)

		fn_executor_obj = executor(target=wrk_fn, args=(fn, params_str, calling_ip))
		fn_executor_obj.deamon = True
		fn_executor_obj.start()

		return serialize('duplex')

	return wrapped_fn

f = lambda x : x
executor = InlineExecutor()

subject = duplex_wrapper(f, executor)

print(subject())