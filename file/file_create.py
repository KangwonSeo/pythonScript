f1=open('1page__.txt', 'r')
f2=open('2page__.txt', 'r')
f3=open('3page__.txt', 'r')
f4=open('4page__.txt', 'r')
f=open('all.txt', 'w')
fileList = [f1, f2, f3, f4]
for i in fileList:
    while True:
        line = i.readline()
        if not line: break
        f.write(line)

f1.close()
f2.close()
f3.close()
f4.close()
f.close()
