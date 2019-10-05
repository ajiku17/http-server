from urllib import parse

class httpRequest:

	def __init__(self, request):
		self.headers = {}
		stringRepr = request.decode()
		lines = stringRepr.split('\r\n')
		requestLine =  lines[0].split()
		self.method = requestLine[0].lower()
		self.url = parse.unquote(requestLine[1])
		self.version = requestLine[2].lower()

		for line in lines[1:-2]:
			header = line.split(': ')
			self.headers[header[0].lower()] = header[1].lower()



	def getVersion(self):
		return self.version

	def getMethod(self):
		return self.method

	def getURL(self):
		return self.url


	def setHeader(self, header, value):
		self.headers[header.lower()] = value.lower()

	def getHeaderValue(self, header):
		return self.headers.get(header.lower(), None)

	def containsHeader(self, header):
		return header.lower() in self.headers






class httpResponse:

	statusMessages = {200 : 'OK',
					  404 : 'Not Found',
					  306 : 'Partial Content'}

	def __init__(self):
		self.version = 'HTTP/1.1'
		self.headers = {}
		self.entity = bytes()

	
	def headToString(self):
		res = self.version + ' ' + str(self.statusCode) + ' ' + self.statusMessage + '\r\n'
		for header in self.headers:
			res += header + ': ' + str(self.headers[header]) + '\r\n'
		res += '\r\n'
		return res


	def setVersion(self, version):
		self.version = version.lower()

	def setStatusCode(self, statusCode):
		self.statusCode = statusCode
		self.statusMessage = self.statusMessages.get(statusCode, 'Blank Message')

	def setStatusMessage(self, statusMessage):
		self.statusMessage = statusMessage

	
	def getVersion(self):
		return self.version

	def getStatusCode(self):
		return self.statusCode

	def getStatusMessage(self):
		return self.statusMessage


	def setHeader(self, header, value):
		self.headers[header.lower()] = value.lower()

	def getHeaderValue(self, header):
		return self.headers.get(header.lower(), None)


	def containsHeader(self, header):
		return header.lower() in self.headers


	def setEntity(self, data):
		self.entity = data
		self.headers['content-length'] = str(len(data))

	def getEntity(self):
		return self.data


	def toBytes(self):
		res = self.headToString()
		return res.encode() + self.entity