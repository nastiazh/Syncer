import time
import os.path as Path
from syncercore import File
from syncercore import Socket
from syncercore import Syncer

syncer = Syncer('localhost',1234, 'test')

#always sync folder every 3 seconds
while True:
	syncer.sync()
	time.sleep(3)
