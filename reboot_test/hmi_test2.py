# -*- coding: utf-8 -*-
import serial
import time
#import datetime
import signal
import threading
import sys
import msvcrt
import ctypes
#from datetime import date
import datetime
import os
import logging



line = [] #라인 단위로 데이터 가져올 리스트 변수

cpu_port = 'COM3' # 시리얼 포트
mcu_port = 'COM6'
relay_port = 'COM9'

cpu_baud = 115200 # 시리얼 보드레이트(통신속도)
relay_baud = 9600 # 파워제어 릴레이 속도

use_relay = 0    #만약 relay를 이용해서 on/off하는 경우는 1, 아니면 0

exitThread = False   # 쓰레드 종료용 변수
timer_counter = 0
cycle_counter = 0
job_step = 0
exit_with_normal_mode = 0
start_ts = 0
pre_step = 0
hmi_ok = 0
hmi_counter = 0
agl_counter = 0
map_counter = 0
retry_counter = 0
ioc_ok = 0
map_ok = 0

#쓰레드 종료용 시그널 함수
def handler(signum, frame):
     exitThread = True

def processing():
      global job_step
      global ser
      global exit_with_normal_mode
      global timer_counter
      global exitThread
      global cycle_counter
      global start_ts
      global pre_step
      global hmi_ok
      global hmi_counter
      global agl_counter
      global retry_counter
      global map_counter
      global ser_relay
      global ioc_ok
      global map_ok
	  
#      ff = open(filename, mode='at', encoding='utf-8')
      
      if job_step == 0:
           hmi_ok = 0
           ioc_ok = 0
           map_ok = 0
           retry_counter = 0
           logger.info("                ")
           logger.info("_____ Starting (%d) (%s)", cycle_counter+1, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))
           start_ts = time.time()	
           if use_relay == 1:	   
              ser_relay.write(b'\xa0\x01\x00\xa1')
           job_step = 1
		   
      elif job_step == 1:
#           ser_power.write(b'OUTP ON\n')
           logger.info("__________ WakeUp (%f)", (time.time() - start_ts) )	   
           job_step = 2
           timer_counter = 0
 
      elif job_step == 2:   # qnx mode
           if timer_counter >= 50:
#              exitThread = True	
              logger.error ("AGL ready ???..........")
              job_step = 10
           
      elif job_step == 3:
           logger.info	("__________ AGL ready (%f)" , (time.time() - start_ts) )	   
           timer_counter = 0
           job_step = 10
	
      elif job_step == 10:
           if timer_counter >= 10:
#               ser.write(b'telnet 192.168.0.7\n')
               ser.write(b'ssh -q -o StrictHostKeyChecking=no root@192.168.0.7\n')
               job_step = 30
               timer_counter = 0

      elif job_step == 30:
           if timer_counter >= 20:
               ser.write(b'\n')
               timer_counter = 0
               retry_counter += 1
               logger.error("__________ ssh retry (%d, %f)", retry_counter, time.time() - start_ts)

               if retry_counter >= 10:
                  if use_relay == 1:	
                     job_step = 100
                     timer_counter = 0
                  else:
#                     exitThread = True
                     print("aaa")
#                     sys.exit()

               elif retry_counter >= 2:
                 job_step = 10
                 timer_counter = 0
            
      elif job_step == 40:
           agl_counter+=1
           logger.info("__________ ssh connected (%f)" ,(time.time() - start_ts) )
           job_step = 90
           timer_counter = 0
           if cycle_counter == 0:
              ser.write(b'rm -rf /var/lib/nav/coredump/* \n')
              ser.write(b'sync\n')
              job_step = 90
              timer_counter = 0
			   
      elif job_step == 55:
           if timer_counter >= 2:
               ser.write(b'systemctl --failed\n')
               job_step = 90
               timer_counter = 0
               
      elif job_step == 90:
           if timer_counter >= 2:
               ser.write(b'ls -al /var/lib/nav/coredump\n')
               job_step = 93
               timer_counter = 0

      elif job_step == 91:
           if timer_counter >= 5:
#               ser.write(b'/lge/app_ro/bin/rsi-send -h ::1 --pretty -p 49600 get /displaymanagement/renderingSurfaces/ \n')
#               ser.write(b'/tmp/USB/PORT2/PART1/check_hmi.sh\n')
               ser.write(b'/usr/bin/check_hmi.sh\n')               
               job_step = 95
               timer_counter = 0

      elif job_step == 92:
           if timer_counter >= 2:
               ser.write(b'export XDG_RUNTIME_DIR=/early/user/0\n')
               hmi_ok = 0
               job_step = 93
               timer_counter = 0

      elif job_step == 93:
           if timer_counter >= 2:
               ser.write(b'LayerManagerControl get surface 16\n')
               job_step = 95
               timer_counter = 0
               
      elif job_step == 95:
           retry_counter = 0
           if hmi_ok == 1:
               hmi_counter+=1
               logger.info("__________ HMI OK(%f)" ,(time.time() - start_ts) )				   
               job_step = 96
               timer_counter = 0
           if timer_counter >= 5:
               job_step = 96
               timer_counter = 0

      elif job_step == 96:
           if timer_counter >= 10:
               map_ok = 0
               ser.write(b'curl -L [::1]:80/navsystem/systems/ | grep \'status\'\n')
               job_step = 98
               timer_counter = 0

      elif job_step == 98:
           if map_ok == 1:
               map_counter+=1
               logger.info("__________ MAP OK(%f)" ,(time.time() - start_ts) )				   
               job_step = 99
               timer_counter = 0
               
           if map_ok == 2:
               logger.debug("__________ MAP loading(%f)" ,(time.time() - start_ts) )		
               retry_counter+=1               
               job_step = 96
               timer_counter = 0
           
           if timer_counter >= 5:
               retry_counter+=1               
               job_step = 96
               timer_counter = 0

           if retry_counter >= 10:
               job_step = 99
               timer_counter = 0
               logger.error("__________ MAP is not visible(%f)" ,(time.time() - start_ts) )		
      
      elif job_step == 99:
           ser.write(b'top -b -i -n 1\n')
           job_step = 100 
           timer_counter = 0

      elif job_step == 100:
           if timer_counter >= 2:
               cycle_counter+=1
#               print ( "             ")
#               print    ("____________________ Result..........(", cycle_counter, "), agl ok=", agl_counter, "hmi ok=", hmi_counter, "map ok=", map_counter )
               logger.info ("____________________ Result..........(%d), agl ok(%d), hmi ok(%d), map ok(%d)" ,cycle_counter, agl_counter, hmi_counter, map_counter )
               job_step = 110 
               timer_counter = 0

      elif job_step == 110:
           if timer_counter >= 3:
               if use_relay ==1:
                  ser_relay.write(b'\xa0\x01\x01\xa2')    # can off
#               ser_power.write(b'OUTP OFF\n')
               else: 
                  ser.write(b'/usr/bin/mcu_reset.sh\n')   # mcu reset
  #             print ("__________ Goto BusSleep (", time.time() - start_ts, ")")
               logger.info("__________ Goto BusSleep (%f)" , (time.time() - start_ts) )				   
               if use_relay == 1:
                  job_step = 115 
               else:
                  job_step = 120   
               timer_counter = 0

      elif job_step == 115:
           if timer_counter >= 100:
               if ioc_ok == 1:
  #                print ("__________ Bus Sleep OK (", time.time() - start_ts, ")")
                  logger.info("__________ Bus Sleep OK (%f)" , (time.time() - start_ts) )				   
               else:
  #                print ("__________ Bus Sleep error (", time.time() - start_ts, ")")
                  logger.error("__________ Bus Sleep error (%f)" , (time.time() - start_ts) )				   
               
               job_step = 120 
               timer_counter = 0
                                
      elif job_step == 120:
           if timer_counter >= 5:
               job_step = 0 
  #             print("__________ Cycle end(", time.time() - start_ts, ")")
               logger.info("__________ Cycle end(%f)" , (time.time() - start_ts) )				   


      if pre_step != job_step:
         logger.debug("................................. step=%d, time=%f", job_step, time.time() - start_ts)
      pre_step = job_step
			  
#      ff.close()
      

# rx 데이터 처리할 함수
def parsing_data(data):
    global job_step
    global hmi_ok
    global ioc_ok
    global map_ok
	
    # 리스트 구조로 들어 왔기 때문에
    # 작업하기 편하게 스트링으로 합침
    tmp = ''.join(data)
    tmp = tmp.replace("\n", "")  
    #출력!
#    print(tmp)
	
#    if find_MMI_State in tmp:
#        print(tmp)
#        exitThread = True
#    if job_step == 0:
#        if tmp.find("Automotive Grade Linux 3.0.0+snapshot-20190422") >= 0:
#           job_step = 1

    if job_step == 2:
       if tmp.find("ttyAMA0") >= 0:
          job_step = 3
#          print("AGL ready")
	
#    if job_step == 20:
#       if tmp.find("Connected to") >= 0:
#          job_step = 50

    if job_step == 30:
       if tmp.find("root@8x96autogvmquin:~#") >= 0:
          job_step = 40
#          print("telnet connected")


#    if job_step >= 10:
#       tmp.strip(b'\r')
#       tmp.strip(b'\n')    
#       print('%s' %tmp)

    if tmp.find("AGL Boot Start") >= 0:
       logger.info ("__________ AGL Boot Start (%f)", time.time() - start_ts)
 
    if tmp.find("AGL Boot Checked") >= 0: 
       logger.info ("__________ AGL Boot Checked (%f)", time.time() - start_ts)

    if tmp.find("[PWR] state: MMI_STBY") >= 0: 
       logger.info ("__________ MMI_STBY (%f)", time.time() - start_ts)

    if tmp.find("[PWR] state: MMI_STBY_PWRSAV1") >= 0: 
       logger.info ("__________ MMI_STBY_PWRSAV1 (%f)", time.time() - start_ts)

    if tmp.find("[PWR] state: MMI_IOC") >= 0: 
       logger.info ("__________ MMI_IOC (%f)", time.time() - start_ts)
       ioc_ok = 1
      
       
#    if tmp.find("inet6 addr:") >= 0:
#       print("_____" '%s' %tmp)       
    
#    ff.write(tmp)

#    ff = open(filename, mode='at', encoding='utf-8')
#    ff.write ("[%s]:%s" % ((time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))), tmp))
#    ff.close()
    logger.debug("%s" ,tmp)

    if tmp.find("x=0, y=0, w=1560, h=700") >= 0:
       hmi_ok =1

    if tmp.find("operable") >= 0:
       map_ok =1

    if tmp.find("starting") >= 0:
       map_ok = 2
       
#    if tmp.find(" : 1560") >= 0:
#       hmi_ok =1	   
	   
#본 쓰레드
def readThread(ser):
    global line
    global exitThread

    # 쓰레드 종료될때까지 계속 돌림
    while not exitThread:
        #데이터가 있있다면
        for c in ser.read():
#         line = ser.readline()
            #line 변수에 차곡차곡 추가하여 넣는다.
            line.append(chr(c))

            if c == 10: #라인의 끝을 만나면..
                #데이터 처리 함수로 호출
#                line.strip(b'\r')
#                line.strip(b'\n')    
                parsing_data(line)

                #line 변수 초기화
                del line[:]                


def readThread2(ser):
    global line
    global exitThread

    while not exitThread:

        line = ser.readline()    
        print(line)
        line.strip(b'\r')
        line.strip(b'\n')    
        print(line)
        parsing_data(line)

if __name__ == "__main__":
    #종료 시그널 등록
    signal.signal(signal.SIGINT, handler)
    
    if len(sys.argv) < 2: 
        print("COMPORT is not selected") 
        print("usage: 'python hmi_test.py COM2' ")
        sys.exit()
    
    print(sys.argv[1])
    
    if not os.path.isdir("log"):
       os.mkdir("log")
       print ("make log directory")   
	
#    ff = open('log.txt', mode='at', encoding='utf-8')
    
#    today = date.today()
#    filename = "\\log\\"+str(today)+".txt"

    today = datetime.datetime.now()
    nowDatetime = today.strftime('%Y-%m-%d_%H_%M')
    filename = ".\\log\\"+str(nowDatetime)+".txt"
#    filename = now.strftime('%Y-%m-%d-%H')+".txt"
    
#    ff = open(filename, mode='at', encoding='utf-8')
	
    logger = logging.getLogger('myapp')
	
    formatter = logging.Formatter('%(asctime)s - %(levelname)s : %(message)s')
#    logPath = './log' + 
  
#    loggerLevel = logging.NOTSET
#    loggerLevel = logging.DEBUG
#    loggerLevel = logging.INFO
#    loggerLevel = logging.WARN
#    loggerLevel = logging.ERROR
#    loggerLevel = logging.CRITICAL
    logger.setLevel(logging.DEBUG)
    
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)
    streamHandler.setLevel(logging.INFO)
    logger.addHandler(streamHandler)

    fileHandler = logging.FileHandler(filename)
    fileHandler.setFormatter(formatter)
    fileHandler.setLevel(logging.DEBUG)
    logger.addHandler(fileHandler)
#    loggerHandler = logging.FileHandler(logPath)




    #시리얼 열기
    ser = serial.Serial(sys.argv[1], cpu_baud, timeout=0)
#    ser_power = serial.Serial('COM4', 19200, timeout=0)

    if use_relay ==1:
       ser_relay = serial.Serial(relay_port, relay_baud, timeout=0)

    #시리얼 읽을 쓰레드 생성
    thread = threading.Thread(target=readThread, args=(ser,))

    #시작!
    thread.start()
	
    while not exitThread:
#    while not msvcrt.kbhit() or msvcrt.getch() != " ": 
       timer_counter+=1
       time.sleep(1)
       if cycle_counter >= 5000:
         exitThread = True	
       processing()
	   
    print ("___EXIT___")
#    ser_power.close()
    ser.close()
    time.sleep(2)
#    ff.close()
	
    sys.exit(0)
	