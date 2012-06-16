import sys
import math

def roundup(x):
    return int(math.ceil(x / 512.0)) * 512

def zero(x):
    for i in x:
        if i != '\0': return False
    return True

def checksum(x):
    c = 0
    for i in x: c += ord(i)
    return list(('%06o\0 ' % c))

def tar(f):    
    uid = ['0']*7 + ['\0']
    f = open(f, 'rb+')
    c = 0
    while (True):
        data = list(f.read(512))
        if len(data) == 0: break
        elif len(data) != 512: print "ERROR"
        elif zero(data):
            if c == 1: break
            c+=1
            continue
        c = 0
        data[108:116] = uid
        data[116:124] = uid
        data[148:156] = [' ']*8
        data[148:156] = checksum(data)
        size = roundup(int(''.join(data[124:135]), 8))
        f.seek(-512, 1)
        f.write(''.join(data))
        d = f.seek(size, 1)    
    f.close()
    

if sys.argv[1][-3:] == 'tar':
    tar(sys.argv[1])
elif sys.argv[1] == 'version':
    exec(open("../../python/gui.py", "r").read().split('\n')[1])
    f = open('control/control', 'r').read().split('\n')
    f[1] = 'Version: %s-1' % version
    open('control/control', 'w').write('\n'.join(f))
    