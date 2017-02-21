import time
import os.path as Path
from syncercore import File
from syncercore import Socket
from syncercore import Syncer

syncer = Syncer('195.133.145.48',1234, '/usr/bin/python3.5')

#always sync folder every 3 seconds
while True:
	syncer.sync()
	time.sleep(3)
