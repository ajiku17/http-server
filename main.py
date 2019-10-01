import threading
import socket
import sys
import json
import magic
from urllib import parse


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

	lines = request.strip().split('\r\n')
	# print(lines[0])
	requestLine = lines[0]

	resourceUrl = parse.unquote(requestLine.split()[1])
	headers = {}
	for headerLine in lines[1:]:
		# print(headerLine)
		headers[headerLine.split(': ')[0].lower()] = headerLine.split(': ')[1].lower()

	# print(headers)
	host = headers['host'].split(':')[0]
	response = bytes()
	# print(host)
	# print(vhosts)
	if host in vhosts:
		docRoot = vhosts[host]
		fullPath = docRoot + resourceUrl
		try:
			# print(fullPath)
			resource = open(fullPath, 'rb').read()
			mime = magic.Magic(mime=True)
			contentType = mime.from_file(fullPath)
			resposnseStr = 'HTTP/1.1 200 OK\r\nServer: santinos_server\r\nConnection: close\r\nDate: sup\r\nEtag: ra_ubedurebaa\r\nContent-Type: ' + contentType + '\r\nContent-Length: ' + str(len(resource)) + '\r\n\r\n'
			response = resposnseStr.encode()
			# print(response)

			if requestLine.split()[0].lower() == 'get':
				response = response + resource
			
		except:
			response = 'HTTP/1.1 404 Not Found\r\n\r\n'.encode()
	else:
		response = ('HTTP/1.1 404 Not Found\r\nContent-Length:' + str(len('REQUESTED DOMAIN NOT FOUND'.encode())) + '\r\n\r\nREQUESTED DOMAIN NOT FOUND').encode()

	return response




def requestHandler(conn, addr, vhosts):
	requestLine = conn.recv(1024).decode()
	fullRequest = requestLine
	while not fullRequest.endswith('\r\n\r\n'):
		line = conn.recv(1024).decode()
		# print(line)
		fullRequest = fullRequest + line

	# print(fullRequest)

	response = processRequest(fullRequest, vhosts)

	conn.send(response)

	conn.close()



def serverHandler(serverAddr, vhosts):
	print(serverAddr)
	
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
	s.bind(serverAddr)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.listen(10)

	while True:
		conn, addr = s.accept()
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
		print(hosts)
		serverThread = threading.Thread(target=serverHandler, args=(s, hosts))
		serverThread.start()
	


readConfig()
main()


