from struct import pack  
import json

class JsonEncoder:
	def __init__(self, Header: str = 'CHAR', OUT='NO', IN='YES'):  
		self.Out = open(f'{OUT}.jsfb', 'wb')  
		self.In = open(f'{IN}.json', 'r')
		self.Header = Header  

	def WriteHeader(self):  
		self.Out.write(pack('<I', 16))  
		self.Out.write(pack('4s', self.Header.encode()))
		self.Out.write(pack('<3H', 6, 8, 4))
		self.Out.write(pack('<2I', 6, 4))

	def WriteJSONStructures(self):
		pass

	def ExportJSFB(self):
		pass

