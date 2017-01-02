import json
import os
import os.path as Path
import socket
import time

class File:
	def build_tree(path='.', files={}):
		try:
			#scan folder
			for file in os.listdir(path):
				#build path
				file_addr = path+'/'+file
				#if dir run recursion
				if Path.isdir(file_addr):
					File.build_tree(file_addr, files)
				else:
					#add file to our files
					files[file_addr] = int(Path.getmtime(file_addr))
		except FileNotFoundError:
			print("Folder '"+path+"' doesn't exist! Create it.")
			os.mkdir(path)
			File.build_tree(path)
		return files
	
	def open(file_name, mode):
		path = file_name.split('/')
		built_path = ''
		for folder in path[:-1]:
			built_path += folder + '/'
			if not Path.exists(built_path):
				os.mkdir(built_path)
		return open(file_name, mode)
	
	def rmdir(path):
		if Path.isdir(path):
			for file in os.listdir(path):
				built_path = path+'/'+file
				if Path.isdir(built_path):
					File.rmdir(built_path)
				else:
					os.remove(built_path)
			
		
class Socket:
	def download_file(socket, name, size, edition_time=None):
		tmp_file = File.open(name+'.tmp', 'wb+')
		try:
			while size > 0:
				buf = socket.recv(1024)
				tmp_file.write(buf)
				tmp_file.flush()
				size -= len(buf)
		except KeyboardInterrupt:
			print('Cant receive file '+name)
		finally:
			tmp_file.close()
		os.rename(name+'.tmp', name)
		if edition_time:
			os.utime(name, (edition_time, edition_time))

		
	def upload_file(socket, name):
		file = File.open(name,'rb')
		try:
			data = file.read(1024)
			while len(data) > 0:
				socket.send(data)
				data = file.read(1024)
		except KeyboardInterrupt:
			print('Cant send file '+name+' to the server')
		finally:
			file.close()
			
	def send_command(socket, data):
		try:
			json_line = (json.dumps(data)+'\n').encode('utf-8')
			socket.send(json_line)
		except KeyboardInterrupt:
			print('Cand send command:'+str(data))
			
		
	def receive_command(socket):
		done = False
		json_line = ''
		json_data = []
		sym = ''
		try:
			while sym != '\n':
				sym = socket.recv(1).decode('utf-8')
				json_line += sym
			json_data = json.loads(json_line)
		except KeyboardInterrupt:
			print('Cant receive command. Json line:\n'+json_line)
		return json_data
	
	def close_connection(socket):
		Socket.send_command(socket, {"command":"bye"})
		if Socket.receive_command(socket)["response"] == 'bye':
			print('Server accepted closing')
		socket.close()
		
class Syncer:
	def __init__(self, server, port, folder='.', modelfile='filestructure.json'):
		self.server = server
		self.port = port
		self.folder = folder
		self.model = modelfile
		
		self.removing_sync()
		
	def removing_sync(self):
		real = File.build_tree(self.folder)
		mod = self.read_model()
		for key in mod.keys():
			if not real.get(key):
				print("Removing from server "+key)
				self.remove_from_server(key)
		self.write_model(real)
		
	def read_model(self):
		mod = {}
		if Path.exists(self.model):
			mod = json.load(File.open(self.model,'r'))
		else:
			mod = File.build_tree(self.folder)
			json.dump(mod, File.open(self.model,'w+'))
		return mod
	
	def write_model(self, model):
		json.dump(model, File.open(self.model,'w+'))
	
	#NOT SUPPORTED BY SERVER
	def remove_from_server(self, filename):
		sock = socket.socket()
		sock.connect((self.server, self.port))
		
		Socket.send_command(sock, {"command":"delete", "file":filename})
		resp = Socket.receive_command(sock)['response']
		print(resp)
		if resp == 'OK':
			print('File '+ filename+' has removed')
		else:
			print('An exception occured when remove file '+filename)
		Socket.close_connection(sock)
	
	def sync_local(self):
		sock = socket.socket()
		sock.connect((self.server, self.port))
		
		Socket.send_command(sock,{"command":"sync", "folder":self.folder})
		local_files = File.build_tree(self.folder)
		server_files = Socket.receive_command(sock)['files']
		
		to_download = []
		to_upload = []
		
		for key in server_files.keys():
			if local_files.get(key):
				if server_files[key] == local_files[key]:
					del local_files[key]
					continue
				to_download.append(key) if server_files[key] > local_files[key] else to_upload.append(key)
				del local_files[key]
			else:
				to_download.append(key)
		to_upload.extend(local_files)
		
		#downloading files
		for file in to_download:
			print('Downloading '+file+'\t',end='')
			Socket.send_command(sock, {'command':'get','file':file})
			response = Socket.receive_command(sock)
			print(response)
			if response['response'] == 'OK':
				Socket.download_file(sock, file, response['filesize'], server_files[file])
				Socket.send_command(sock, {'status':'DONE'})
			else:
				print('file not exist on server!')
			print("DONE")
		
		#uploading files
		for file in to_upload:
			print('Uploading '+file+'\t',end='')
			Socket.send_command(sock, {'command':'send','filename':file,'filesize':Path.getsize(file), "filetime":int(Path.getmtime(file))})
			if Socket.receive_command(sock)['response'] == 'OK':
				Socket.upload_file(sock, file)
				print(Socket.receive_command(sock)['status'])
		Socket.close_connection(sock)
		#self.write_model(File.build_tree(self.folder))
	
	def sync(self):
		self.removing_sync()
		self.sync_local()
