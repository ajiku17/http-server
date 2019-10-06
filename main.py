import threading
import socket
import sys
import json
import magic
import os
from time import time, localtime, strftime
from httpMessage import httpResponse, httpRequest
from email.utils import formatdate

TIMEOUT = 5
MAX_KEEP_ALIVE = 200

config = {}


def readConfig():
	global config
	try:
		configFile = open(sys.argv[1])
		config = json.loads(configFile.read().lower())
		os.mkdir(config['log'])
	except:
		print('Could not open configurations file')
		exit()


def generateResponse(request, vhosts):
	response = httpResponse()
	response.setStatusCode(404)
	host = request.getHeaderValue('host').split(':')[0]
	persistance = request.getHeaderValue('connection')
	if host not in vhosts:
		response.setStatusCode(404)
		response.setEntity('REQUESTED DOMAIN NOT FOUND'.encode())
		return response, False

	
	docRoot = vhosts[host]
	fullPath = docRoot + request.getURL()

	response.setHeader('server', 'santinos_server')
	response.setHeader('date', formatdate(timeval=None, localtime=False, usegmt=True))
	response.setHeader('etag', os.path.getmtime(fullPath))
	response.setHeader('accept-ranges', 'bytes')
	response.setHeader('content-length', 0)
	response.setHeader('connection', 'keep-alive' if persistance == 'keep-alive' else 'close')
	if persistance == 'keep-alive':
		response.setHeader('keep-alive', 'timeout=' + str(TIMEOUT) + ', max=' + str(MAX_KEEP_ALIVE))


	try:
		resource = open(fullPath, 'rb')
		response.setHeader('content-type', magic.Magic(mime=True).from_file(fullPath))

		if request.containsHeader('if-none-match'):
			etag = request.getHeaderValue('if-none-match')
			if etag == str(os.path.getmtime(fullPath)):
				response.setStatusCode(304)
				return response, response.getHeaderValue('connection') == 'keep-alive'

		if request.containsHeader('range'):
			
			response.setStatusCode(206)
			byteRange = request.getHeaderValue('range')
			byteOffsets = byteRange.split('=')[1].split('-')
			start = int(byteOffsets[0])
			
			resource.seek(start)
			
			end = -1
			if byteOffsets[1]:
				end = int(byteOffsets[1])
				response.setHeader('content-range', byteRange + '/' + str(os.path.getsize(fullPath)))
				if request.getMethod == 'head':
					response.setHeader('content-length', end - start + 1)
				else:
					response.setEntity(resource.read(end - start + 1))

			else:
				response.setHeader('content-range', byteRange + '/' + str(os.path.getsize(fullPath)))
				if request.getMethod == 'head':
					response.setHeader('content-length', str(os.path.getsize(fullPath)) - start + 1)
				else:
					response.setEntity(resource.read())

		else:
			response.setStatusCode(200)
			data = resource.read()
			if request.getMethod() == 'head':
				response.setHeader('content-length', str(os.path.getsize(fullPath)))
			else:
				response.setEntity(data)

	except Exception as e:
		print(e)
		response.setStatusCode(404)
		return response, False

	return response, response.getHeaderValue('connection') == 'keep-alive'

# this isnt thread safe
def writeLog(vhosts, logDir, date, ipAddr, request, response):
	host = request.getHeaderValue('host').split(':')[0]
	log = [strftime("[%a %b %d %H:%M:%S %Y]", date), ipAddr, host, request.getURL(), str(response.getStatusCode()),
					 response.getHeaderValue('content-length'), request.getHeaderValue('user-agent')]
	
	logPath = logDir + '/' + (host if host in vhosts else 'error') + '.log'
	if host in vhosts:
		f = open(logDir + '/' + host + '.log', 'a')
		f.write(' '.join(log))
		f.write('\n')
		# f.write('\n')
		# print(logDir + '/' + host + '.log')
	else:
		f = open(logDir + '/error.log', 'a')
		f.write(' '.join(log))
		f.write('\n')
		# f.write('\n')
		# print(logDir + '/error.log')


	# print(logPath)
	# f = open(logPath, 'a')
	# f.write(' '.join(log))
	# f.write('\n')



def requestHandler(conn, addr, vhosts):
	try:
		for i in range(MAX_KEEP_ALIVE):
			request = conn.recv(1024)
			while not request.endswith(b'\r\n\r\n'):
				line = conn.recv(1024)
				request += line

			# print(request.decode())

			request = httpRequest(request)

			dateReceived = localtime()

			logDir = config['log']

			response, keepAlive = generateResponse(request, vhosts)

			writeLog(vhosts, logDir, dateReceived, addr[0], request, response)
			
			conn.send(response.toBytes())

			if not keepAlive: 
				break

	except Exception as e: 
		print(e)
		conn.close()
	finally:
		conn.close()



def serverHandler(serverAddr, vhosts):
	
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
	s.bind(serverAddr)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.listen(1024)

	while True:
		conn, addr = s.accept()
		conn.settimeout(TIMEOUT)
		connThread = threading.Thread(target=requestHandler, args=(conn, addr, vhosts))
		connThread.start()


	s.close()



def main():
	socketAddresses = set()

	for s in config['server']:
		socketAddresses.add((s['ip'], s['port']))

	for s in socketAddresses:
		hosts = {}
		for y in [(x['vhost'], x['documentroot']) for x in config['server'] if x['ip'] == s[0] and x['port'] == s[1]]:
			hosts[y[0]] = y[1]

		serverThread = threading.Thread(target=serverHandler, args=(s, hosts))
		serverThread.start()
	


readConfig()
main()


