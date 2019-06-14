#!/usr/bin/env python

# WS client example

import websocket
import os
import base64
import datetime
import curve25519
import json
import pyqrcode
import io
import random
import logging

from utilities import *
from threading import Timer
from os.path import expanduser
from whatsapp_binary_reader import whatsappReadBinary

try:
    import thread
except ImportError:
    import _thread as thread
import time

home = expanduser("~")
settingsDir = home + "/.wweb"
settingsFile = settingsDir + '/data.json'
subscribeList = settingsDir + '/subscribe.json'
presenceFile = settingsDir + '/presence.json'

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

if not os.path.exists(settingsDir):
    os.makedirs(settingsDir)

class WhatsApp:

    ws = None
    mydata = None
    clientId = None
    privateKey = None
    publicKey = None
    secret = None
    encKey = None
    macKey = None
    sharedSecret = None
    data = {}
    mydata = {}
    sessionExists = False

    def initLocalParams(self):
        print('Entering Initlocalparms')
        self.data = self.restoreSession()
        keySecret = None
        if self.data is None:
            self.mydata['clientId'] = base64.b64encode(os.urandom(16))
            keySecret = os.urandom(32)
            self.mydata["keySecret"] = base64.b64encode(keySecret)
            
        else:
            self.sessionExists = True
            self.mydata = self.data['myData']
            keySecret = base64.b64decode(self.mydata["keySecret"])

        print('Keysecret', keySecret)
        self.clientId = self.mydata['clientId']
        self.privateKey = curve25519.Private(secret=keySecret)
        self.publicKey = self.privateKey.get_public()
        print('Privatekey',self.privateKey)
        print('ClientId', self.clientId)
        print('Exiting Initlocalparms')

        if self.sessionExists:
            self.setConnInfoParams(base64.b64decode(self.data["secret"]))

    def sendKeepAlive(self):
        Timer(25, lambda: self.ws.send('?,,')).start()

    def saveSession(self, jsonObj):
        jsonObj['myData'] = self.mydata
        if self.sessionExists:
            for key, value in jsonObj.iteritems():
                self.data[key] = value
            jsonObj = self.data
        with open(settingsFile, 'w') as outfile:
            json.dump(jsonObj, outfile)

    def restoreSession(self):
        if(os.path.exists(settingsFile)):
            with open(settingsFile) as file:
                data = json.load(file)
                return data
        return None

    def subscribe(self):
        with open(subscribeList) as f:
            lineList = f.readlines()
            for line in lineList:
                self.sendSubscribe(str.strip(line))

    def sendSubscribe(self, userId):
        print("Subsrcibing for", userId)
        messageTag = str(getTimestampMs())
        message = ('%s,,["action", "presence", "subscribe", "%s@c.us"]' % (messageTag, userId))
        print(message)
        self.ws.send(message)

    def writePresenceToFile(self, userId, pType, pTime):
        with open(presenceFile, "a+") as pFile:
            pFile.write('%s %s %s\n' % (userId, pType, str(pTime)))

    def setConnInfoParams(self, secret):
        self.secret = secret
        self.sharedSecret = self.privateKey.get_shared_key(curve25519.Public(secret[:32]), lambda a: a)
        sharedSecretExpanded = HKDF(self.sharedSecret, 80)
        hmacValidation = HmacSha256(sharedSecretExpanded[32:64], secret[:32] + secret[64:])
        if hmacValidation != secret[32:64]:
            raise ValueError("Hmac mismatch")

        keysEncrypted = sharedSecretExpanded[64:] + secret[64:]
        keysDecrypted = AESDecrypt(sharedSecretExpanded[:32], keysEncrypted)
        self.encKey = keysDecrypted[:32]
        self.macKey = keysDecrypted[32:64]

    def handleBinaryMessage(self, message):
        checkSum = message[:32]
        hashHMAC = HmacSha256(self.macKey, message[32:])
        if hashHMAC != checkSum:
            logging.info("Invalid Checksum")
            raise ValueError
        decryptedMessage = AESDecrypt(self.encKey,  message[32:])
        processedData = whatsappReadBinary(decryptedMessage, True);
        logging.info("Actual Message: %s", processedData)

    def on_message(self, ws, message):
        try:
            messageSplit = message.split(",", 1)
            if len(messageSplit) == 1:
                logging.info('Single index message: %s', message)
                return
            messageTag = messageSplit[0]
            messageContent = messageSplit[1]
            logging.info("Message Tag: %s", messageTag)

            try:
                jsonObj = json.loads(messageContent)
                logging.info("Raw msg: %s", message)
            except:
                logging.info("Error in loading message and messagecontent")
                self.handleBinaryMessage(messageContent)
            else:
                if 'ref' in jsonObj:
                    if self.sessionExists is False:
                        serverRef = json.loads(messageContent)["ref"]
                        qrCodeContents = serverRef + "," + base64.b64encode(self.publicKey.serialize()) + "," + self.clientId
                        svgBuffer = io.BytesIO();											# from https://github.com/mnooner256/pyqrcode/issues/39#issuecomment-207621532
                        img = pyqrcode.create(qrCodeContents, error='L')
                        img.svg(svgBuffer, scale=6, background="rgba(0,0,0,0.0)", module_color="#122E31", quiet_zone=0)
                        print(img.terminal(quiet_zone=1))
                elif isinstance(jsonObj, list) and len(jsonObj) > 0:
                    if jsonObj[0] == "Conn":
                        print("Connection msg received")
                        self.sendKeepAlive()
                        if self.sessionExists is False:
                            self.setConnInfoParams(base64.b64decode(jsonObj[1]["secret"]))
                        self.saveSession(jsonObj[1])
                        self.subscribe()
                    elif jsonObj[0] == "Cmd":
                        print("Challenge received")
                        cmdInfo = jsonObj[1]
                        if cmdInfo["type"] == "challenge":
                            challenge = base64.b64decode(cmdInfo["challenge"])
                            sign = base64.b64encode(HmacSha256(self.macKey, challenge))
                            print('sign',sign)
                            messageTag = str(getTimestamp())
                            message = ('%s,["admin","challenge","%s","%s","%s"]' % (messageTag, sign, self.data["serverToken"], self.clientId))
                            print('message', message)
                            ws.send(message)
                    elif jsonObj[0] == "Presence":
                        presenceInfo = jsonObj[1]
                        userId = presenceInfo["id"]
                        presencetype = presenceInfo["type"]
                        presenceTime = getTimestampMs()
                        self.writePresenceToFile(userId, presencetype, presenceTime)
                elif isinstance(jsonObj, object):
                    print('Chance of status')
                    status = jsonObj["status"]
                        
                            

        except:
            print("Some error encountered")
            raise

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws):
        print("### closed ###")

    def on_open(self, ws):
        print("Socket Opened")
        print("ClientId", self.clientId)
        messageTag = str(getTimestamp())
        message = messageTag + ',["admin","init",[0,3,2390],["Chromium at ' + datetime.datetime.now().isoformat() + '","Chromium"],"' + self.clientId + '",true]'
        print(message)
        ws.send(message)

        if self.data is not None:
            clientToken = self.data["clientToken"]
            serverToken = self.data["serverToken"]
            messageTag = str(getTimestamp())
            message = ('%s,["admin","login","%s","%s","%s","takeover"]' % (messageTag, clientToken, serverToken, self.clientId))
            print(message)
            ws.send(message)
        else:
            print("No data")
        
    
    def connect(self):
        self.initLocalParams()
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp("wss://w1.web.whatsapp.com/ws/",
                                on_message = lambda ws,msg: self.on_message(ws, msg),
                                on_error = lambda ws, msg: self.on_error(ws, msg),
                                on_close = lambda ws: self.on_close(ws),
                                on_open = lambda ws: self.on_open(ws),
                                header = { "Origin: https://web.whatsapp.com" })

        self.ws.run_forever()


if __name__ == "__main__":
    WhatsApp().connect()
