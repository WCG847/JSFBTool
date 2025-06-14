from struct import unpack, error as StructError
from typing import BinaryIO
from io import BytesIO
import string
import json




class Jsfb:
	def ReadHeader(self, JSFB):
		try:
			Offset = unpack("<I", JSFB.read(4))[0]
		except StructError:
			raise ValueError("Failed to unpack header — file too short or corrupt")

		JSFB.seek(Offset + 8)
		try:
			self.Count = unpack("<I", JSFB.read(4))[0]
		except StructError:
			raise ValueError("Failed to unpack Count — malformed table header")

		TableSize = self.Count << 2
		VTable = JSFB.read(TableSize)

		if len(VTable) < TableSize:
			raise ValueError("VTable size mismatch — possibly corrupted")

		self.VTable = BytesIO(VTable)
		self.TotalSize = ((TableSize + 4) + Offset) + 4

		JSFB.seek(0, 2)
		file_size = JSFB.tell()

		if self.TotalSize > file_size:
			raise ValueError(f"TotalSize ({self.TotalSize}) exceeds file size ({file_size})")

		JSFB.seek(self.TotalSize)
		Data = JSFB.read(file_size - self.TotalSize)
		self.Data = BytesIO(Data)

		# Read header string
		JSFB.seek(4)
		raw_header = JSFB.read(4)
		if len(raw_header) < 4:
			raise ValueError("Header string not found")
		self.Header = unpack('4s', raw_header)[0].decode('latin1')

		JSFB.close()

	def ResolveVTable(self):
		self.Info = []

		# Validate entire VTable range
		self.VTable.seek(0, 2)
		vtable_size = self.VTable.tell()
		self.VTable.seek(0)

		for i in range(self.Count):
			cp = self.VTable.tell()
			raw1 = self.VTable.read(4)
			if len(raw1) < 4:
				raise ValueError(f"VTable read error at index {i}: incomplete Offset1")

			Offset1 = unpack("<I", raw1)[0]

			if i + 1 < self.Count:
				raw2 = self.VTable.read(4)
				if len(raw2) < 4:
					raise ValueError(f"VTable read error at index {i}: incomplete Offset2")
				Offset2 = unpack("<I", raw2)[0]
				Size = Offset1 - Offset2
				self.VTable.seek(cp + 4)
			else:
				self.Data.seek(0, 2)
				end_of_data = self.Data.tell()
				if Offset1 > end_of_data:
					raise ValueError(f"Field {i} Offset1 out of bounds: {Offset1} > {end_of_data}")
				Size = end_of_data - Offset1

			if Size < 0:
				raise ValueError(f"Field {i} has negative size: {Size} — invalid offset logic")

			self.Info.append({
				"Index": i,
				"Offset": Offset1,
				"Size": Size,
			})

		return self.Info

	def ExportPointer(self, wantedIndex, file, Schema: dict = None, name='OUT'):
		self.YourJSON = {
			'header': self.Header
		}

		entry = next((e for e in self.Info if e["Index"] == wantedIndex), None)
		if not entry:
			raise IndexError(f"Index {wantedIndex} not found in VTable")

		Offset = entry['Offset']
		Size = entry['Size']

		with open(file, 'rb') as JSFB:
			JSFB.seek(0, 2)
			file_size = JSFB.tell()

			if Offset + Size > file_size:
				raise ValueError(f"ExportPointer: Field offset+size ({Offset + Size}) exceeds file size ({file_size})")

			JSFB.seek(Offset)
			block = JSFB.read(Size)

			def is_likely_string(data: bytes) -> bool:
				if not data or b'\x00' in data[:-1]:  # allow final null, but not mid-null
					return False
				try:
					decoded = data.decode('utf-8')
				except UnicodeDecodeError:
					try:
						decoded = data.decode('latin1')
					except UnicodeDecodeError:
						return False
				# Check if all chars are printable (space or better)
				return all(c in string.printable for c in decoded)

			if Schema is None:
				if is_likely_string(block):
					try:
						self.YourJSON['string'] = block.decode('utf-8')
					except UnicodeDecodeError:
						self.YourJSON['string'] = block.decode('latin1')
				else:
					# Default to DWORD readout
					JSFB.seek(Offset)
					for i in range(Size // 4):
						raw = JSFB.read(4)
						if len(raw) < 4:
							self.YourJSON[f'unknown{i}'] = 'incomplete'
						else:
							self.YourJSON[f'unknown{i}'] = unpack('<I', raw)[0]

		with open(f'{name}.json', 'w') as OUTSIDE:
			json.dump(self.YourJSON, OUTSIDE, indent=4)