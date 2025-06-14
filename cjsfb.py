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
			Offset1 = unpack("<I", self.VTable.read(4))[0]

			# Peek ahead only if there's another field
			if i + 1 < self.Count:
				Offset2 = unpack("<I", self.VTable.read(4))[0]
				Size = Offset1 - Offset2
				# Reset to simulate sliding window
				self.VTable.seek(cp + 4)
			else:
				self.Data.seek(0, 2)
				Size = self.Data.tell() - Offset1



			self.Info.append(
				{
					"Index": i,
					"Offset": Offset1,
					"Size": Size,
				}
			)
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

