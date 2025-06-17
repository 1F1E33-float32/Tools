import struct

ver000 = {
'HDR_SIZE' : 0x0,    # base header size
'HDRAS_POS': None,   # offset of additional header data size (set to None if not used)

'STR_TYPE': 0x3,     # string type identifier
'FILE_TYPE': 0x7F,   # file type identifier

'TEXT_FCN': 0x140,   # function id for text command (set to None if not used)
'BKLG_FCN': 0x143,   # function id for backlog text command (set to None if not used)
'RUBY_FCN': 0x14B,   # function id for ruby command (set to None if not used)

'NAME_POS': 0x24,    # offset of TXT_FCN from name argument
'TEXT_POS': 0x2C,    # offset of TXT_FCN from text argument
'RUBYK_POS': 0x14,   # offset of RUBY_FCN from kanji argument
'RUBYF_POS': 0x0C,   # offset or RUBY_FCN from furigana argument
'BKLG_POS': 0x0C,    # offset of BKLG_FCN from text argument
}

# header beginning with "BurikoCompiledScriptVer1.00"
ver100 = {
'HDR_SIZE': 0x1C,    # base header size
'HDRAS_POS': 0x1C,   # offset of additional header data size (set to None if not used)

'STR_TYPE': 0x3,     # string type identifier
'FILE_TYPE': 0x7F,   # file type identifier

'TEXT_FCN': 0x140,   # function id for text command (set to None if not used)
'BKLG_FCN': 0x143,   # function id for backlog text command (set to None if not used)
'RUBY_FCN': 0x14B,   # function id for ruby command (set to None if not used)

'NAME_POS': 0x0C,    # offset of TXT_FCN from name argument
'TEXT_POS': 0x04,    # offset of TXT_FCN from text argument
'RUBYK_POS': 0x04,   # offset of RUBY_FCN from kanji argument
'RUBYF_POS': 0x0C,   # offset or RUBY_FCN from furigana argument
'BKLG_POS': 0x0C,    # offset of BKLG_FCN from text argument
}

# select which version based on known header string
def get_config(data):
	if data.startswith(b'BurikoCompiledScriptVer1.00\x00'):
		config = ver100
	else:
		config = ver000
	return config

def get_dword(data, offset):
	bytes = data[offset:offset + 4]
	if len(bytes) < 4:
		return None
	return struct.unpack('<I', bytes)[0]

def get_section_boundary(data):
	data_len = len(data)

	for i in range(0, data_len, 1):
		segment = data[i - 8:i]
		if segment == b'\x00\x00\x00\x00\x01\x00\x00\x00':
			start_index = i - 4
			break
		if segment == b'\x00\x00\x00\x00\x10\x00\x00\x00':
			start_index = i -4
			break

	for i in range(start_index, data_len, 1):
		segment = data[i - 4:i]
		if segment == b'\xF4\x00\x00\x00' or segment == b'\x1B\x00\x00\x00':
			end_index = i
	print(start_index, end_index)
	return start_index, end_index
	
def split_data(data):
	config = get_config(data)
	start_b, end_b = get_section_boundary(data)
	code_bytes = data[start_b:end_b]
	text_bytes = data[end_b:]
	return code_bytes, text_bytes, config

def get_text_section(text_bytes):
	strings = text_bytes.split(b'\x00')
	addrs = []
	pos = 0
	for string in strings:
		addrs.append(pos)
		pos += len(string) + 1
	texts = [x.decode('cp932') for x in strings]
	text_section = {}
	for addr,text in zip(addrs,texts):
		text_section[addr] = text
	return text_section
	
def check(code_bytes, pos, cfcn, cpos):
	return get_dword(code_bytes, pos + cpos) == cfcn
	
def get_code_section(code_bytes, text_section, config):
	with open('code.bin', 'wb') as f:
		f.write(code_bytes)
	pos = 4
	code_size = len(code_bytes)
	code_section = {}
	index = 0

	while pos < code_size:
		type = get_dword(code_bytes, pos - 4)
		dword = get_dword(code_bytes, pos)
		text_addr = dword - code_size
		# check if address is in text section and data type is string or file
		if text_addr in text_section:
			text = text_section[text_addr]
			if type == config['STR_TYPE']:
				if check(code_bytes, pos, config['TEXT_FCN'], config['NAME_POS']): # check if name (0140)
					comment = 'NAME'

				elif check(code_bytes, pos, config['TEXT_FCN'], config['TEXT_POS']): # check if text (0140)
					comment= 'TEXT'

				elif check(code_bytes, pos, config['RUBY_FCN'], config['RUBYK_POS']): # check if ruby kanji (014b)
					comment = 'TEXT RUBY KANJI'

				elif check(code_bytes, pos, config['RUBY_FCN'], config['RUBYF_POS']): # check if ruby furigana (014b)
					comment = 'TEXT RUBY FURIGANA'

				elif check(code_bytes, pos, config['BKLG_FCN'], config['BKLG_POS']): # check if backlog text (0143)
					comment = 'TEXT BACKLOG'

				else:
					comment = 'OTHER'
				code_section[index] = (comment, text)
				index += 1

			elif type == config['FILE_TYPE']:
				pass
			
		pos += 4
	return code_section