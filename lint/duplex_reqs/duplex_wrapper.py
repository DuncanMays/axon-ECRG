wraps fn in the needed for duplex communication pattern
# adds code to deserialize parameters from the request and return its results through the a separate request
def duplex_wrapper(fn, executor):

	def wrapped_fn():

		# this function will run in a separate thread, will execute the RPC and return the result with a POST request
		def wrk_fn(fn, params_str, calling_ip):

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
			data = {'result': serialize(return_object), 'id': serialize(call_id)}
			
			# TODO: this should be wrapped in a try/except for the case when the caller isn't listenning, this is a common case since a simplex stub would start the RPC but not listen for a response
			x=requests.post(url=url, data=data)

		params_str = route_req.form['msg']
		calling_ip = route_req.remote_addr

		# because flask, and WSGI servers in general, cannot schedule code to execute after a route completes, inline duplex RPCs would have to send the returning request before the calling request completes
		# to prevent this, we must run the RPC in a separate thread, and to preserve synchronous bahavior, we must use a threadlock with other inline RPCs. This will ensure no two inline RPCs are executing at the same time.
		fn_executor = None
		if(executor == InlineExecutor):

			def inline_lock_fn(fn, params_str, calling_ip):
				with inline_lock:
					result = wrk_fn(fn, params_str, calling_ip)

				return result

			fn_executor = Thread(target=inline_lock_fn, args=(fn, params_str, calling_ip))
		else:
			fn_executor = executor(target=wrk_fn, args=(fn, params_str, calling_ip))

		fn_executor.deamon = True
		fn_executor.start()

		return serialize('duplex')

	return wrapped_fn