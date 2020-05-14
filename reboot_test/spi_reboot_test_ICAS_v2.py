import serial
import time
import signal
import threading
import sys
import msvcrt
import ctypes
import logging
import signal, os

from datetime import datetime
baud = 115200

shutDownCmd = 'echo control 2 2 > /dev/vmm\n'
checkCmd = 'pidin | grep "qvm" | wc -l\n'
rebootCmd = 'qon -d /vm/images/start_agl.sh restart\n'
resetCount = failCount = 0
EventList = []
sleepTime = 10
idxAction = 0
idxEvent = 1
idxHandler = 2

def signalHandler(signum, frame):
    exitThread = True
    print ("___EXIT___")
    time.sleep(1)
    ser.close()
    exit()
    
def waitBoot():
    bootEvent.wait()
    
def parsing_data(data):
    tmp = ''.join(data)
    tmp = tmp.replace("\n", "")
    
    if tmp.find("AGL Boot Checked") >= 0:
        bootEvent.set()
    
    for i in EventList:
        if tmp.find(i[idxEvent]) >= 0:
            i[idxHandler]()
    
def readThread(ser):
    line = []
    NewLine = 10
    while not exitThread:
        for c in ser.read():
            line.append(chr(c)) 
            if c == NewLine:
#                print(''.join(line))
                logging.info(''.join(line)) #print all log.
                parsing_data(line)
                del line[:]   

def setupLog():
    today = datetime.today()
    currentPath = os.path.dirname(os.path.abspath(__file__))
    logDir = currentPath+'/log'
    logFile = logDir+'/test'+str(today.month)+'-'+str(today.day)
    if not os.path.exists(logDir):
        os.makedirs(logDir)
        
    if os.path.isfile(logFile):
        os.remove(logFile)
    logging.basicConfig(filename=logFile, level=logging.DEBUG)

def actionLog():
    global failCount
    failCount += 1
    logging.debug("failCount = " + str(failCount) )
    print("failCount = " + str(failCount) )
    
def addEvent(action, event, handler):
    global EventList
    EventList.append([action, event, handler])

def doAction():
    for i in EventList:
        if i[idxAction] is not None:
            ser.write(i[idxAction].encode())
            time.sleep(sleepTime)    
    time.sleep(sleepTime)
    
# main #
if len(sys.argv) < 2:
    print("python spi_reboot_test_ICAS_v2.py <comport> <sleeptime>\n")
    print("eg. python spi_reboot_test_ICAS_v2.py COM3 100\n")
    sys.exit()
    
ser = serial.Serial(sys.argv[1], baud, timeout=0)

if len(sys.argv) > 2:
    sleepTime = int(sys.argv[2])
    
setupLog()
exitThread = False
thread = threading.Thread(target=readThread, args=(ser,))
bootEvent = threading.Event()
failLock = threading.Lock()
thread.start()
signal.signal(signal.SIGINT, signalHandler)

addEvent(None, "Comm: systemd-cgroups", actionLog)

while True:
    logging.debug("loop start") 
    waitBoot()

    resetCount += 1
    logging.debug("resetCount = " + str(resetCount)) 
    print("resetCount = " + str(resetCount)) 
    
    doAction()
    
    ser.write(shutDownCmd.encode())
    for i in range(0,5):
        time.sleep(1)
        ser.write(checkCmd.encode())

    ser.write(rebootCmd.encode())

exitThread = True
print ("___EXIT___")
ser.close()
