import threading
import socket
import sys
import json
import magic
import os
from urllib import parse
from time import time

TIMEOUT = 5
MAX_KEEP_ALIVE = 200

config = {}


def readConfig():
	global config
	try:
		configFile = open(sys.argv[1])
		config = json.loads(configFile.read().lower())
	except:
		print('Could not open configurations file')
		exit()


# vhost = {hostname : document root}
def processRequest(request, vhosts):
	# print(request)
	lines = request.strip().split('\r\n')
	requestLine = lines[0]
	resourceUrl = parse.unquote(requestLine.split()[1])
	headers = {}
	for headerLine in lines[1:]:
		headers[headerLine.split(': ')[0].lower()] = headerLine.split(': ')[1].lower()

	# print(headers)
	host = headers['host'].split(':')[0]
	persistance = headers.get('connection', 'close')
	
	response = bytes()
	resource = bytes()
	if host in vhosts:
		docRoot = vhosts[host]
		fullPath = docRoot + resourceUrl
		try:
			connectionHeader = 'Connection: '
			if persistance == 'keep-alive':
				connectionHeader = connectionHeader + 'keep-alive\r\nKeep-Alive: timeout=' + str(TIMEOUT) + ', max=' + str(MAX_KEEP_ALIVE) + '\r\n'
			else:
				connectionHeader = connectionHeader + 'Close\r\n'
			
			if 'range' in headers:
				byteRange = headers['range']
				byteOffsets = byteRange.split('=')[1].split('-')
				start = int(byteOffsets[0])
				end = -1
				if byteOffsets[1]:
					end = int(byteOffsets[1])
				
				f = open(fullPath, 'rb')
				f.seek(start)
				
				if end == -1:
					resource = f.read()
				else:
					resource = f.read(end - start + 1)

				mime = magic.Magic(mime=True)
				contentType = mime.from_file(fullPath)

				responseStr = 'HTTP/1.1 206 Partial Content\r\nServer: santinos_server\r\nAccept-Ranges: bytes\r\n' + connectionHeader + 'Date: sup\r\nEtag: ra_ubedurebaa\r\nContent-Type: ' + contentType + '\r\nContent-Length: ' + str(len(resource)) + '\r\nContent-Range: bytes ' + byteOffsets[0] + '-' + byteOffsets[1] + '/' + str(os.path.getsize(fullPath)) + '\r\n\r\n'
			else:
				resource = open(fullPath, 'rb').read()
				mime = magic.Magic(mime=True)
				contentType = mime.from_file(fullPath)
				
				responseStr = 'HTTP/1.1 200 OK\r\nServer: santinos_server\r\nAccept-Ranges: bytes\r\n' + connectionHeader + 'Date: sup\r\nEtag: ra_ubedurebaa\r\nContent-Type: ' + contentType + '\r\nContent-Length: ' + str(len(resource)) + '\r\n\r\n'


			# print(responseStr)
			response = responseStr.encode()
			if requestLine.split()[0].lower() == 'get':
				response = response + resource
			
		except Exception as e:
			print(e)
			response = 'HTTP/1.1 404 Not Found\r\n\r\n'.encode()
	else:
		response = ('HTTP/1.1 404 Not Found\r\nContent-Length:' + str(len('REQUESTED DOMAIN NOT FOUND'.encode())) + '\r\n\r\nREQUESTED DOMAIN NOT FOUND').encode()

	return response, persistance == 'keep-alive'



def requestHandler(conn, addr, vhosts):
	try:
		for i in range(MAX_KEEP_ALIVE):
			requestLine = conn.recv(1024).decode()
			fullRequest = requestLine
			while not fullRequest.endswith('\r\n\r\n'):
				line = conn.recv(1024).decode()
				# print(line)
				fullRequest = fullRequest + line

			start = time()
			response, keepAlive = processRequest(fullRequest, vhosts)
			# print(keepAlive)
			conn.send(response)
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
	# socket.setdefaulttimeout(TIMEOUT)

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

	# print(socketAddresses)
	for s in socketAddresses:
		hosts = {}
		for y in [(x['vhost'], x['documentroot']) for x in config['server'] if x['ip'] == s[0] and x['port'] == s[1]]:
			hosts[y[0]] = y[1]

		serverThread = threading.Thread(target=serverHandler, args=(s, hosts))
		serverThread.start()
	


readConfig()
main()


