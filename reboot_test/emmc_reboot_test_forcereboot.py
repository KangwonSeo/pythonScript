import serial
import time
import signal
import threading
import sys
import msvcrt
import ctypes

baud = 115200
sleepTime = 20
statusFlag = "none"
bootDone = ReadyDone = LogInDone = False
resetCount = partitionRecoverCount = fsckOkCount = 0

def waitBoot():
    if bootDone:
        return True      
    time.sleep(1)    
    return False

def typeEnter():
    if ReadyDone:
        return True    
    ser.write(loginCmd1.encode())
    time.sleep(1)
    return False

def Login():
    if LogInDone:
        return True
    time.sleep(1)
    ser.write(loginCmd2.encode())
    return False
    
def parsing_data(data):
    global bootDone
    global ReadyDone
    global LogInDone
    global partitionRecoverCount
    global fsckOkCount

    tmp = ''.join(data)
    tmp = tmp.replace("\n", "")

    if statusFlag == "none":
        return
    
    if statusFlag == "bootWaiting":
        if tmp.find("##### Last Shutdwon was not OK") >= 0:
            bootDone = True            
        if tmp.find("Filesystem(/dev/mmcblk0p51) fsck OK[1]") >= 0:
            partitionRecoverCount += 1
        if tmp.find("Filesystem(/dev/mmcblk0p51) fsck OK[0]") >= 0:
            fsckOkCount += 1
            
    if statusFlag == "LogInReady":
        if tmp.find("8x96auto login:") >= 0:
            ReadyDone = True
            
    if statusFlag == "LogIn":
        if tmp.find("root@8x96auto:~#") >= 0:
            LogInDone = True        
            

def readThread(ser):
    line = []
    while not exitThread:
        for c in ser.read():
            line.append(chr(c)) 
            if c == 10:
                print(''.join(line))
                parsing_data(line)
                del line[:]   

# main #
exitThread = False

print(sys.argv[1])

ser = serial.Serial(sys.argv[1], baud, timeout=0)

loginCmd1 = '\r\n'
loginCmd2 = 'root\n'
IOCCmd = '/lge/app_ro/bin/ksend -s 0x200000000 -d 0x200000000 -b \"0x01 0x00 0x00 0x00\"\n'
exitThread = False
thread = threading.Thread(target=readThread, args=(ser,))
thread.start()

while True:

    statusFlag = "bootWaiting"
    while True:
        if waitBoot():
            break
    time.sleep(3)
    
    resetCount += 1 
    print("resetCount = ", resetCount) 
    print("partitionRecoverCount = ", partitionRecoverCount);
    print("fsckOkCount = ", fsckOkCount);
    statusFlag = "LogInReady"
    while True:
        if typeEnter():
            break
    
    statusFlag = "LogIn"
    while True:
        if Login():
            break 

    statusFlag = "none"
    time.sleep(sleepTime)
    
    statusFlag = "Reset"           
    ser.write(IOCCmd.encode())  
    
    time.sleep(5)
    bootDone = ReadyDone = LogInDone = False


exitThread = True
print ("___EXIT___")
ser.close()
