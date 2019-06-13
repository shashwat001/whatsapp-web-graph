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

from utilities import *
from threading import Timer
from os.path import expanduser

try:
    import thread
except ImportError:
    import _thread as thread
import time

home = expanduser("~")
settingsDir = home + "/.wweb"
settingsFile = settingsDir + '/data.json'

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

    def sendKeepAlive(self):
        Timer(25, lambda: self.ws.send('?,,')).start()

    def saveSession(self, jsonObj):
        jsonObj['myData'] = self.mydata
        print(jsonObj)
        print("Settings file: ", settingsFile)
        with open(settingsFile, 'w') as outfile:
            json.dump(jsonObj, outfile)

    def restoreSession(self):
        if(os.path.exists(settingsFile)):
            with open(settingsFile) as file:
                data = json.load(file)
                return data
        return None

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

    def on_message(self, ws, message):
        try:
            messageSplit = message.split(",", 1)
            messageTag = messageSplit[0]
            messageContent = messageSplit[1]
            print("Message Tag", messageTag)

            try:
                jsonObj = json.loads(messageContent)
                print("Raw msg: ", message)
            except:
                print("Error in loading message and messagecontent")
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
        if self.data is not None:
            clientToken = self.data["clientToken"]
            serverToken = self.data["serverToken"]
            message = ('%s,["admin","login","%s","%s","%s","takeover"]' % (messageTag, clientToken, serverToken, self.clientId))
            print(message)
            ws.send(message)
        else:
            print("No data")
        message = messageTag + ',["admin","init",[0,3,2390],["Chromium at ' + datetime.datetime.now().isoformat() + '","Chromium"],"' + self.clientId + '",true]'
        print(message)
        ws.send(message)
    
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
