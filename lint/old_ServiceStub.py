class ServiceStub():

	def __init__(self, ip_addr='localhost', endpoint_prefix=default_service_config['endpoint_prefix'], name='', profile=None):
		
		self.profile = None
		self.ip_addr = ip_addr
		self.endpoint_prefix = endpoint_prefix
		self.name = name

		if (profile == None):
			url = 'http://'+str(self.ip_addr)+':'+str(comms_config.worker_port)+'/'+self.endpoint_prefix+self.name
			_, profile_str = GET(url)
			profile = deserialize(profile_str)

		self.set_profile(profile)

	def set_profile(self, profile):

		self.profile = profile

		for key in self.profile.keys():

			# __profile_flag__ always maps to True and exists to distinguish between profiles and RPC configurations
			# __class__ maps to a type, which we don't need here and comes with a whole can of worms tied in knots I don't understand
			if (key == '__profile_flag__' or key=='__class__'): continue

			# the serialized representation of a remote object
			member = self.profile[key]
			# will be set to an object that accesses the remote object represented by member
			attribute = None

			if '__profile_flag__' in member:
				# member is a profile for a ServiceNode
				if member['__profile_flag__']:
					# this should always execute since __profile_flag_always maps to True
					if '__call__' in member:
						# if the remote object represented by profile is callable, it will have a __call__ key. It might have useful attributes if it's callable, so we can't represent it with an attribute-less RPC stub. What we'll do instead is make the stub's __call__ attribute an RPC stub
						attribute = CallableServiceStub(member['__call__'], ip_addr=self.ip_addr, endpoint_prefix=self.endpoint_prefix+'/'+key, name=self.name, profile=member)

					else:
						attribute = ServiceStub(ip_addr=self.ip_addr, endpoint_prefix=self.endpoint_prefix+'/'+key, name=self.name, profile=member)

				else:
					# this means something is very wrong
					raise(BaseException('service profile with __profile_flag__ set to False'))

			else:

				# member is a configuration dict for an RPC
				comms_pattern = member['comms_pattern']

				if (comms_pattern == 'simplex'):
					attribute = CoroSimplexStub(worker_ip=self.ip_addr, endpoint_prefix=self.endpoint_prefix+'/', rpc_name=key)

				elif (comms_pattern == 'duplex'):
					attribute = CoroDuplexStub(worker_ip=self.ip_addr, endpoint_prefix=self.endpoint_prefix+'/', rpc_name=key)

				else:
					raise BaseException('unrecognised communication pattern:'+str(comms_pattern))


			setattr(self, key, attribute)
	

class CallableServiceStub(ServiceStub):

	def __init__(self, self_config, *args, **kwargs):
		ServiceStub.__init__(self, *args, **kwargs)

		# self_config is a configuration dict for an RPC
		comms_pattern = self_config['comms_pattern']

		if (comms_pattern == 'simplex'):
			self.___call___ = CoroSimplexStub(worker_ip=self.ip_addr, endpoint_prefix=self.endpoint_prefix+'/', rpc_name='__call__')

		elif (comms_pattern == 'duplex'):
			self.___call___ = CoroDuplexStub(worker_ip=self.ip_addr, endpoint_prefix=self.endpoint_prefix+'/', rpc_name='__call__')

		else:
			raise BaseException('unrecognised communication pattern:'+str(comms_pattern)) 

	async def __call__(self, *args, **kwargs):
		return await self.___call___(*args, **kwargs)