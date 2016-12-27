import socketserver
import json

class TcpFileHandler(socketserver.BaseRequestHandler):
    def handle(self):
        print('handle request!')
        headers = self.request.recv(1024).decode('utf-8')
        headers = json.loads(headers)
        print(headers['name'])
        #recive acception
        self.request.sendall(b'OK')
        #send file
        file_stream = open(headers['name'],'wb+')
        real_size = 0
        while real_size < headers['size']:
            buff = self.request.recv(1024)
            file_stream.write(buff)
            file_stream.flush()
            real_size += len(buff)
        print(headers['name']+' received')
        self.request.sendall("test done!".encode('utf-8'))

# TODO: watch function
#       sending file
if __name__ == '__main__':
    try:
        server = socketserver.TCPServer(('',1234), TcpFileHandler)
        print('server created!')
        server.serve_forever()
    except KeyboardInterrupt:
        print('bye!')
