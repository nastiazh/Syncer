import socket
import os
import os.path as Path
from syncercore import File
from syncercore import Socket


sock = socket.socket()
sock.bind(('',1234))
sock.listen(10)
print('Server started!')
while True:
	try:
		client, addr = sock.accept()
		print('Connected from '+str(addr))
		#create variable for while
		command = 'start'
		while command:
			command = Socket.receive_command(client)
			print('Received command: '+str(command))
			
			if command['command'] == 'sync':
				files = File.build_tree(command['folder'],{})
				Socket.send_command(client, {"files":files})
				
			elif command['command'] == 'get':
				print('Send '+command['file'],end='')
				if Path.exists(command['file']):
					Socket.send_command(client,{'response':'OK', 'filesize':Path.getsize(command['file'])})
					Socket.upload_file(client, command['file'])
					print(Socket.receive_command(client)['status'])
				else:
					Socket.send_command(client,{'response':'NOT_EXIST'})	
				
			elif command['command'] == 'send':
				print('Receive '+command['filename'],end='')
				Socket.send_command(client,{'response':'OK'})
				Socket.download_file(client, command['filename'], command['filesize'], command['filetime'])
				Socket.send_command(client,{'status':'DONE'})
			
			elif command['command'] == 'delete':
				try:
					os.unlink(command['file'])
					Socket.send_command(client, {'response':'OK'})
				except Exception:
					Socket.send_command(client, {'response':'ServerException'})
			
			elif command['command'] == 'bye':
				Socket.send_command(client,{'response':'bye'})
				client.close()
				command = None
			
			else:
				Socket.send_command(sock,{'response':'UnknownCommand'})
		
		print('\n')
	except Exception:
		print('An exception occured!!!')
