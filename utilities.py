from __future__ import print_function

import sys
import time
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
import hashlib
import hmac
import os
import datetime

from pytz import timezone, utc



def eprint(*args, **kwargs):							# from https://stackoverflow.com/a/14981125
	print(*args, file=sys.stderr, **kwargs)

def getTimestamp():
	return int(time.time())

def getTimestampMs():
	return int(round(time.time() * 1000))

def getTimeString(timezoneStr):
    tz = timezone(timezoneStr)
    fmt = '%Y-%m-%d %H:%M:%S'
    tm = datetime.datetime.now(tz)
    return tm.strftime(fmt)

def mergeDicts(x, y):									# from https://stackoverflow.com/a/26853961
	if x is None and y is None:
		return
	z = (y if x is None else x).copy()
	if x is not None and y is not None:
		z.update(y)
	return z

def getAttr(obj, key, alt=None):
	return obj[key] if isinstance(obj, dict) and key in obj else alt

def filterNone(obj):
	if isinstance(obj, dict):
		return dict((k, filterNone(v)) for k, v in obj.iteritems() if v is not None)
	elif isinstance(obj, list):
		return [filterNone(entry) for entry in obj]
	else:
		return obj

def getNumValidKeys(obj):
	return len(filter(lambda x: obj[x] is not None, list(obj.keys())))

def encodeUTF8(s):
	if not isinstance(s, str):
		s = strng.encode("utf-8")
	return s



def ceil(n):											# from https://stackoverflow.com/a/32559239
	res = int(n)
	return res if res == n or n < 0 else res+1

def floor(n):
	res = int(n)
	return res if res == 0 or n >= 0 else res-1

def HmacSha256(key, sign):
    return hmac.new(key, sign, hashlib.sha256).digest()

def HKDF(key, length, appInfo=""):						# implements RFC 5869, some parts from https://github.com/MirkoDziadzka/pyhkdf
    key = HmacSha256("\0"*32, key)
    keyStream = ""
    keyBlock = ""
    blockIndex = 1
    while len(keyStream) < length:
        keyBlock = hmac.new(key, msg=keyBlock+appInfo+chr(blockIndex), digestmod=hashlib.sha256).digest()
        blockIndex += 1
        keyStream += keyBlock
    return keyStream[:length]

def AESPad(s):
    bs = AES.block_size
    return s + (bs - len(s) % bs) * chr(bs - len(s) % bs)

def to_bytes(n, length, endianess='big'):
    h = '%x' % n
    s = ('0'*(len(h) % 2) + h).zfill(length*2).decode('hex')
    return s if endianess == 'big' else s[::-1]

def AESUnpad(s):
    return s[:-ord(s[len(s)-1:])]

def AESEncrypt(key, plaintext):							# like "AESPad"/"AESUnpad" from https://stackoverflow.com/a/21928790
    plaintext = AESPad(plaintext)
    iv = os.urandom(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return iv + cipher.encrypt(plaintext)

def WhatsAppEncrypt(encKey, macKey, plaintext):
    enc = AESEncrypt(encKey, plaintext)
    return HmacSha256(macKey, enc) + enc				# this may need padding to 64 byte boundary

def AESDecrypt(key, ciphertext):						# from https://stackoverflow.com/a/20868265
    iv = ciphertext[:AES.block_size]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = cipher.decrypt(ciphertext[AES.block_size:])
    return AESUnpad(plaintext)

def getNextLexicographicString(input):
    if input is None or input == '':
        return 'A'
    sz = len(input)-1
    output = ""
    carry = 1
    while sz>=0:
        ch = chr(ord(input[sz])+carry)
        if ch > 'Z':
            carry = 1
            ch = 'A'
        else:
            carry = 0
        output = output + ch
        sz = sz-1
    if carry == 1:
        output = output + 'A'
    return output[::-1]

def customTime(*args):
    utc_dt = utc.localize(datetime.datetime.utcnow())
    my_tz = timezone("Asia/Kolkata")
    converted = utc_dt.astimezone(my_tz)
    return converted.timetuple()