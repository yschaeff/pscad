from copy import deepcopy

class Clippy():
	def __init__(self):
		self.buf = None

	def store(self, obj):
		self.buf = deepcopy(obj)

	def load(self):
		return deepcopy(self.buf)
