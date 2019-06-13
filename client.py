#!/usr/bin/env python

# WS client example

import websocket
import os;
import base64;
import datetime;
import curve25519;
import json;
import pyqrcode;
import io;

from utilities import *;
from threading import Timer;

try:
    import thread
except ImportError:
    import _thread as thread
import time

clientId = base64.b64encode(os.urandom(16));
privateKey = curve25519.Private();
publicKey = privateKey.get_public();
settingsDir = "~/.wweb"

if not os.path.exists(settingsDir):
    os.makedirs(settingsDir)

def sendKeepAlive(ws):
    Timer(25, lambda: ws.send('?,,')).start()

def saveSession(jsonObj):
    print(jsonObj)
    settingsFile = settingsDir + '/data.json';
    print("Settings file: ", settingsFile)
    with open(settingsFile, 'w') as outfile:
        json.dump(jsonObj, outfile)

def on_message(ws, message):
    try:
        print("Raw msg: ", message)
        messageSplit = message.split(",", 1);
        messageTag = messageSplit[0];
        messageContent = messageSplit[1];
        print("Message Tag", messageTag)

        try:
            jsonObj = json.loads(messageContent);
        except:
            print("Error in loading messagecontent")
        else:
            if 'ref' in jsonObj:
                serverRef = json.loads(messageContent)["ref"];
                qrCodeContents = serverRef + "," + base64.b64encode(publicKey.serialize()) + "," + clientId;
                svgBuffer = io.BytesIO();											# from https://github.com/mnooner256/pyqrcode/issues/39#issuecomment-207621532
                img = pyqrcode.create(qrCodeContents, error='L');
                img.svg(svgBuffer, scale=6, background="rgba(0,0,0,0.0)", module_color="#122E31", quiet_zone=0);
                print(img.terminal(quiet_zone=1))
            elif isinstance(jsonObj, list) and len(jsonObj) > 0:
                if jsonObj[0] == "Conn":
                    print("Connection msg received")
                    sendKeepAlive(ws)
                    saveSession(jsonObj[1])
                    




    except:
        print("Some error encountered")
        raise

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    
    messageTag = str(getTimestamp());
    message = messageTag + ',["admin","init",[0,3,2390],["Chromium at ' + datetime.datetime.now().isoformat() + '","Chromium"],"' + clientId + '",true]';
    print(message)
    ws.send(message)


if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://w1.web.whatsapp.com/ws/",
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close,
                              header = { "Origin: https://web.whatsapp.com" })

    
    ws.on_open = on_open
    ws.run_forever()
