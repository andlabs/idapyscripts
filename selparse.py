# based on Megazig's modification of Treeki/Ninjifox's sel_parse.py
# modifications made 8 january 2014
import sys
import struct
from idc import *

# dol.py
class DOLHeader(object):
	def __init__(self, data=None):
		self.offsetText = [0 for x in xrange(7)]
		self.offsetData = [0 for x in xrange(11)]
		self.addressText = [0 for x in xrange(7)]
		self.addressData = [0 for x in xrange(11)]
		self.sizeText = [0 for x in xrange(7)]
		self.sizeData = [0 for x in xrange(11)]
		self.addressBSS = 0
		self.sizeBSS = 0
		self.entrypoint = 0
		if data:
			offset = 0
			for x in xrange(7):
				self.offsetText[x] = struct.unpack('>I', data[x*4:x*4+4])[0]
				self.addressText[x] = struct.unpack('>I', data[28+44+x*4:28+44+x*4+4])[0]
				self.sizeText[x] = struct.unpack('>I', data[28+44+28+44+x*4:28+44+28+44+x*4+4])[0]
			for x in xrange(11):
				self.offsetData[x] = struct.unpack('>I', data[28+x*4:28+x*4+4])[0]
				self.addressData[x] = struct.unpack('>I', data[28+44+28+x*4:28+44+28+x*4+4])[0]
				self.sizeData[x] = struct.unpack('>I', data[28+44+28+44+28+x*4:28+44+28+44+28+x*4+4])[0]
				self.addressBSS, self.sizeBSS, self.entrypoint = struct.unpack('>III', data[28+44+28+44+28+44:28+44+28+44+28+44+12])
	def __str__(self):
		out  = ""
		for x in xrange(7):
			out += "offset text: %08x\n" % self.offsetText[x]
		for x in xrange(7):
			out += "address text: %08x\n" % self.addressText[x]
		for x in xrange(7):
			out += "size text: %08x\n" % self.sizeText[x]
		for x in xrange(11):
			out += "offset data: %08x\n" % self.offsetData[x]
		for x in xrange(11):
			out += "address data: %08x\n" % self.addressData[x]
		for x in xrange(11):
			out += "size data: %08x\n" % self.sizeData[x]
		out += "BSS address: %08x\n" % self.addressBSS
		out += "BSS size: %08x\n" % self.sizeBSS
		out += "entrypoint: %08x\n" % self.entrypoint
		return out
	def PrettyPrint(self):
		out  = ""
		out += "offset-- : address- : size----\tText Table\n"
		for x in xrange(7):
			out += "%08x" % self.offsetText[x]
			out += " : %08x" % self.addressText[x]
			out += " : %08x\n" % self.sizeText[x]
		out += "\n"
		out += "offset-- : address- : size----\tData Table\n"
		for x in xrange(11):
			out += "%08x" % self.offsetData[x]
			out += " : %08x" % self.addressData[x]
			out += " : %08x\n" % self.sizeData[x]
		out += "\n"
		out += "BSS address: %08x\n" % self.addressBSS
		out += "BSS size: %08x\n" % self.sizeBSS
		out += "entrypoint: %08x\n" % self.entrypoint
		return out
	def sorted(self, sort=True):
		out = []
		for x in xrange(7):
			if self.addressText[x] != 0:
				out.append(self.addressText[x])
		for x in xrange(11):
			if self.addressData[x] != 0:
				out.append(self.addressData[x])
		if sort:
			out.sort()
		return out

# Struct.py
class StructType(tuple):
	def __getitem__(self, value):
		return [self] * value
	def __call__(self, value, endian='<'):
		if isinstance(value, str):
			return struct.unpack(endian + tuple.__getitem__(self, 0), value[:tuple.__getitem__(self, 1)])[0]
		else:
			return struct.pack(endian + tuple.__getitem__(self, 0), value)

class StructException(Exception):
	pass

class Struct(object):
	__slots__ = ('__attrs__', '__baked__', '__defs__', '__endian__', '__next__', '__sizes__', '__values__')
	int8 = StructType(('b', 1))
	uint8 = StructType(('B', 1))
	
	int16 = StructType(('h', 2))
	uint16 = StructType(('H', 2))
	
	int32 = StructType(('l', 4))
	uint32 = StructType(('L', 4))
	
	int64 = StructType(('q', 8))
	uint64 = StructType(('Q', 8))
	
	float = StructType(('f', 4))

	def string(cls, len, offset=0, encoding=None, stripNulls=False, value=''):
		return StructType(('string', (len, offset, encoding, stripNulls, value)))
	string = classmethod(string)
	
	LE = '<'
	BE = '>'
	__endian__ = '<'
	
	def __init__(self, func=None, unpack=None, **kwargs):
		self.__defs__ = []
		self.__sizes__ = []
		self.__attrs__ = []
		self.__values__ = {}
		self.__next__ = True
		self.__baked__ = False
		
		if func == None:
			self.__format__()
		else:
			sys.settrace(self.__trace__)
			func()
			for name in func.func_code.co_varnames:
				value = self.__frame__.f_locals[name]
				self.__setattr__(name, value)
		
		self.__baked__ = True
		
		if unpack != None:
			if isinstance(unpack, tuple):
				self.unpack(*unpack)
			else:
				self.unpack(unpack)
		
		if len(kwargs):
			for name in kwargs:
				self.__values__[name] = kwargs[name]
	
	def __trace__(self, frame, event, arg):
		self.__frame__ = frame
		sys.settrace(None)
	
	def __setattr__(self, name, value):
		if name in self.__slots__:
			return object.__setattr__(self, name, value)
		
		if self.__baked__ == False:
			if not isinstance(value, list):
				value = [value]
				attrname = name
			else:
				attrname = '*' + name
			
			self.__values__[name] = None
			
			for sub in value:
				if isinstance(sub, Struct):
					sub = sub.__class__
				try:
					if issubclass(sub, Struct):
						sub = ('struct', sub)
				except TypeError:
					pass
				type_, size = tuple(sub)
				if type_ == 'string':
					self.__defs__.append(Struct.string)
					self.__sizes__.append(size)
					self.__attrs__.append(attrname)
					self.__next__ = True
					
					if attrname[0] != '*':
						self.__values__[name] = size[3]
					elif self.__values__[name] == None:
						self.__values__[name] = [size[3] for val in value]
				elif type_ == 'struct':
					self.__defs__.append(Struct)
					self.__sizes__.append(size)
					self.__attrs__.append(attrname)
					self.__next__ = True
					
					if attrname[0] != '*':
						self.__values__[name] = size()
					elif self.__values__[name] == None:
						self.__values__[name] = [size() for val in value]
				else:
					if self.__next__:
						self.__defs__.append('')
						self.__sizes__.append(0)
						self.__attrs__.append([])
						self.__next__ = False
					
					self.__defs__[-1] += type_
					self.__sizes__[-1] += size
					self.__attrs__[-1].append(attrname)
					
					if attrname[0] != '*':
						self.__values__[name] = 0
					elif self.__values__[name] == None:
						self.__values__[name] = [0 for val in value]
		else:
			try:
				self.__values__[name] = value
			except KeyError:
				raise AttributeError(name)
	
	def __getattr__(self, name):
		if self.__baked__ == False:
			return name
		else:
			try:
				return self.__values__[name]
			except KeyError:
				raise AttributeError(name)
	
	def __len__(self):
		ret = 0
		arraypos, arrayname = None, None
		
		for i in range(len(self.__defs__)):
			sdef, size, attrs = self.__defs__[i], self.__sizes__[i], self.__attrs__[i]
			
			if sdef == Struct.string:
				size, offset, encoding, stripNulls, value = size
				if isinstance(size, str):
					size = self.__values__[size] + offset
			elif sdef == Struct:
				if attrs[0] == '*':
					if arrayname != attrs:
						arrayname = attrs
						arraypos = 0
					size = len(self.__values__[attrs[1:]][arraypos])
				size = len(self.__values__[attrs])
			
			ret += size
		
		return ret
	
	def unpack(self, data, pos=0):
		for name in self.__values__:
			if not isinstance(self.__values__[name], Struct):
				self.__values__[name] = None
			elif self.__values__[name].__class__ == list and len(self.__values__[name]) != 0:
				if not isinstance(self.__values__[name][0], Struct):
					self.__values__[name] = None
		
		arraypos, arrayname = None, None
		
		for i in range(len(self.__defs__)):
			sdef, size, attrs = self.__defs__[i], self.__sizes__[i], self.__attrs__[i]
			
			if sdef == Struct.string:
				size, offset, encoding, stripNulls, value = size
				if isinstance(size, str):
					size = self.__values__[size] + offset
				
				temp = data[pos:pos+size]
				if len(temp) != size:
					raise StructException('Expected %i byte string, got %i' % (size, len(temp)))
				
				if encoding != None:
					temp = temp.decode(encoding)
				
				if stripNulls:
					temp = temp.rstrip('\0')
				
				if attrs[0] == '*':
					name = attrs[1:]
					if self.__values__[name] == None:
						self.__values__[name] = []
					self.__values__[name].append(temp)
				else:
					self.__values__[attrs] = temp
				pos += size
			elif sdef == Struct:
				if attrs[0] == '*':
					if arrayname != attrs:
						arrayname = attrs
						arraypos = 0
					name = attrs[1:]
					self.__values__[attrs][arraypos].unpack(data, pos)
					pos += len(self.__values__[attrs][arraypos])
					arraypos += 1
				else:
					self.__values__[attrs].unpack(data, pos)
					pos += len(self.__values__[attrs])
			else:
				values = struct.unpack(self.__endian__+sdef, data[pos:pos+size])
				pos += size
				j = 0
				for name in attrs:
					if name[0] == '*':
						name = name[1:]
						if self.__values__[name] == None:
							self.__values__[name] = []
						self.__values__[name].append(values[j])
					else:
						self.__values__[name] = values[j]
					j += 1
		
		return self
	
	def pack(self):
		arraypos, arrayname = None, None
		
		ret = ''
		for i in range(len(self.__defs__)):
			sdef, size, attrs = self.__defs__[i], self.__sizes__[i], self.__attrs__[i]
			
			if sdef == Struct.string:
				size, offset, encoding, stripNulls, value = size
				if isinstance(size, str):
					size = self.__values__[size]+offset
				
				if attrs[0] == '*':
					if arrayname != attrs:
						arraypos = 0
						arrayname = attrs
					temp = self.__values__[attrs[1:]][arraypos]
					arraypos += 1
				else:
					temp = self.__values__[attrs]
				
				if encoding != None:
					temp = temp.encode(encoding)
				
				temp = temp[:size]
				ret += temp + ('\0' * (size - len(temp)))
			elif sdef == Struct:
				if attrs[0] == '*':
					if arrayname != attrs:
						arraypos = 0
						arrayname = attrs
					ret += self.__values__[attrs[1:]][arraypos].pack()
					arraypos += 1
				else:
					ret += self.__values__[attrs].pack()
			else:
				values = []
				for name in attrs:
					if name[0] == '*':
						if arrayname != name:
							arraypos = 0
							arrayname = name
						values.append(self.__values__[name[1:]][arraypos])
						arraypos += 1
					else:
						values.append(self.__values__[name])
				
				ret += struct.pack(self.__endian__+sdef, *values)
		return ret
	
	def __getitem__(self, value):
		return [('struct', self.__class__)] * value


class SelSectionItem(Struct):
	__endian__ = Struct.BE
	def __format__(self):
		self.addr = Struct.uint32
		self.size = Struct.uint32

class SELHeader(Struct):
	__endian__ = Struct.BE
	def __format__(self):
		self.prev = Struct.uint32
		self.next = Struct.uint32
		self.section_cnt = Struct.uint32
		self.section_off = Struct.uint32
		self.path_offset = Struct.uint32
		self.path_length = Struct.uint32
		self.unk5 = Struct.uint32
		self.unk6 = Struct.uint32

		self.unk7 = Struct.uint32
		self.unk8 = Struct.uint32
		self.unk9 = Struct.uint32
		self.unk10 = Struct.uint32
		self.internalTableOffs = Struct.uint32
		self.internalTablelength = Struct.uint32
		self.externalTableOffs = Struct.uint32
		self.externalTableLength = Struct.uint32

		self.exportTableOffs = Struct.uint32
		self.exportTableLength = Struct.uint32
		self.exportTableNames = Struct.uint32
		self.importTableOffs = Struct.uint32
		self.importTableLength = Struct.uint32
		self.importTableNames = Struct.uint32

	def __str__(self):
		out = ''
		out += '      prev: %08x -       next: %08x -      section_cnt: %08x -  section_off: %08x\n' % (self.prev,self.next,self.section_cnt,self.section_off)
		out += 'ELF Offset: %08x - ELF Length: %08x -      Unk5: %08x -  Unk6: %08x\n' % (self.path_offset,self.path_length,self.unk5,self.unk6)
		out += '      Unk7: %08x -       Unk8: %08x -      Unk9: %08x - Unk10: %08x\n' % (self.unk7,self.unk8,self.unk9,self.unk10)
		out += '     internalTableOffs: %08x -      internalTablelength: %08x -     externalTableOffs: %08x - externalTableLength: %08x\n' % (self.internalTableOffs,self.internalTablelength,self.externalTableOffs,self.externalTableLength)
		out += 'SymbOffset: %08x - SymbLength: %08x - StrOffset: %08x - importTableOffs: %08x\n' % (self.exportTableOffs,self.exportTableLength,self.exportTableNames,self.importTableOffs)
		out += '     importTableLength: %08x -      importTableNames: %08x' % (self.importTableLength,self.importTableNames)
		return out

class Symbol(Struct):
	__endian__ = Struct.BE
	def __format__(self):
		self.str_offset = Struct.uint32
		self.symb_address = Struct.uint32
		self.section = Struct.uint32
		self.elf_hash = Struct.uint32

	def __str__(self):
		return 'StrOffset: %08x - Address: %08x - Section: %08x - ElfHash: %08x - %s' % (self.str_offset,self.symb_address,self.section,self.elf_hash,GetString(self.str_offset))

	## andlabs routine
	def get_addrlabel(self):
		if self.section != 0x3 and self.section != 0x4 and self.section != 10 and self.section != 13 and self.section != 0xfff1 and self.section != 241:
			addr = segments[ segment_naming[self.section] ]+self.symb_address
			return (addr, GetString(self.str_offset))
		else:
			return ()

	def to_idc(self):
		if self.section != 0x3 and self.section != 0x4 and self.section != 10 and self.section != 13 and self.section != 0xfff1 and self.section != 241:
			addr = segments[ segment_naming[self.section] ]+self.symb_address
			return 'MakeFunction(0x%08X, BADADDR); MakeName(0x%08X, "%s");' % (addr,addr,GetString(self.str_offset))
		else:
			return ""

	def to_map(self):
		if self.section != 0x3 and self.section != 0x4 and self.section != 10 and self.section != 13 and self.section != 0xfff1 and self.section != 241:
			addr = segments[ segment_naming[self.section] ]+self.symb_address
			return '\t%s = 0x%08X;' % (GetString(self.str_offset),addr)
		else:
			return ""

def GetString(offset):
	offset += header.exportTableNames
	return data[offset:data.find('\0',offset)]

## and now for andlabs's stuff

def panic(msg):
	print(msg)
	exit()

nFailed = 0

def setLabel(addr, label):
	global nFailed

	err = idc.MakeNameEx(addr, label, idc.SN_PUBLIC)
	if err != 1:
		# don't panic; this smight mean long label
		print("rename 0x%X to %s failed" % (addr, label))
		nFailed = nFailed + 1

def main():
	global data
	global header
	global segments
	global segment_naming
	global nFailed

	filename = idc.AskFile(0, "*.sel", "Open *.sel File")
	if filename is None:
		print("cancelled")
		return

	f = open(filename, 'rb')
	data = f.read()
	f.close()

	DoIDC = ('-idc' in sys.argv)
	MakeMap = ('-map' in sys.argv)

	header = SELHeader()
	header.unpack(data)

	SymbolCount = header.exportTableLength / 0x10
	Symbols = []

	segment_naming = ['None', '_f_init', '_f_text', '_f_ctors', '_f_dtors', '_f_rodata', '_f_data', '_f_bss', '_f_sbss', '_f_sdata2', '_f_zero', '_f_sdata', '_f_sbss2', '_f_zero2' ]
	segments = { }
	for i in xrange(SymbolCount):
		s = Symbol()
		s.unpack(data[header.exportTableOffs+(i*0x10):header.exportTableOffs+(i*0x10)+0x10])
		if s.section == 0xfff1:
			name = GetString(s.str_offset)
			segments[name] = s.symb_address

	for i in xrange(SymbolCount):
		s = Symbol()
		s.unpack(data[header.exportTableOffs+(i*0x10):header.exportTableOffs+(i*0x10)+0x10])
		# TODO the original made a function too
		stuff = s.get_addrlabel()
		if len(stuff) <> 0:
			setLabel(stuff[0], stuff[1])
		Symbols.append(s)

	if nFailed == 0:
		print("success")
	else:
		print("mostly success (%d failed)" % (nFailed))

main()
