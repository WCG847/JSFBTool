from struct import unpack
from typing import BinaryIO
from io import BytesIO
import json


class Jsfb:
	def ReadHeader(self, JSFB):
		Offset, _ = unpack("<2H", JSFB.read(4))
		JSFB.seek(Offset + 8)
		self.Count = unpack("<I", JSFB.read(4))[0]
		TableSize = self.Count << 2
		VTable = JSFB.read(TableSize)
		self.VTable = BytesIO(VTable)
		self.TotalSize = ((TableSize + 4) + Offset) + 4
		JSFB.seek(-self.TotalSize, 2)
		TotalFileSize = JSFB.tell()
		JSFB.seek(self.TotalSize)
		Data = JSFB.read(TotalFileSize)
		self.Data = BytesIO(Data)
		JSFB.seek(4)
		self.Header = unpack('4s', JSFB.read(4))[0].decode('latin1')
		JSFB.close()

	def ResolveVTable(self):
		self.Info = []
		for i in range(self.Count):
			cp = self.VTable.tell()
			Offset1, Offset2 = unpack("<2I", self.VTable.read(8))
			if i + 1 < self.Count:
				Size = Offset1 - Offset2
			else:
				self.Data.seek(0, 2)
				Size = Offset1 - self.Data.tell()
			self.Info.append(
				{	"Index": i,
					"Offset": Offset1,
					"Size": Size,
				}
			)
			self.VTable.seek(cp + 4)
		return self.Info

	def ExportPointer(self, wantedIndex, file, Schema: dict = None, name='OUT'):
		self.YourJSON = {
			'Header': self.Header
			}
		for entry in self.Info:
			if wantedIndex == entry["Index"]:
				Offset = entry['Offset']
				Size = entry['Size']

		with open(file, 'rb') as JSFB:
			JSFB.seek(Offset)
			if Schema == None:
				# assume stride count DWORD
				for i in range(Size // 4):
					data = unpack('<I', JSFB.read(4))[0]
					self.YourJSON[f'Unknown{i}'] = data
		with open(f'{name}.json', 'w') as OUTSIDE:
			json.dump(self.YourJSON, OUTSIDE)

