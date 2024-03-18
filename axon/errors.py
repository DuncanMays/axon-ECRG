
class AxonError(BaseException):

	def __init__(self, message):
		self.message = message
		super().__init__(self.message)


class EndpointUndefined(AxonError):

	def __init__(self, endpoint):
		self.message = f'No RPC registered at endpoint: {endpoint}'
		super().__init__(self.message)