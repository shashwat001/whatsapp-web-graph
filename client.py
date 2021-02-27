#!/usr/bin/python

# WS client example

import base64
import io
import logging
from os.path import expanduser
from threading import Timer

import binascii
import curve25519
import pyqrcode
import websocket

from utilities import *
from whatsapp_binary_reader import whatsappReadBinary
from whatsapp_binary_writer import whatsappWriteBinary
from whatsapp_defines import *;
from worker import Worker

WHATSAPP_WEB_VERSION = "0,4,2081"

try:
    import thread
except ImportError:
    import _thread as thread

home = expanduser("~")
settingsDir = home + "/.wweb"
settingsFile = settingsDir + '/data.json'
loggingDir = settingsDir + "/logs"
subscribeListFile = settingsDir + '/subscribe.json'
presenceFile = settingsDir + '/presence.json'

if not os.path.exists(settingsDir):
  os.makedirs(settingsDir)
if not os.path.exists(loggingDir):
  os.makedirs(loggingDir)



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
  keepAliveTimer = None

  #subscribeTimer is required as whatsapp unsubscribes by itself every 12 hours
  subscribeStarted = False
  subscribeTimer = None
  worker = None
  messageSentCount = 0
  subscriberList = set()

  def __init__(self, worker):
    self.worker = worker

  def initLocalParams(self):
    logging.info('Entering Initlocalparms')
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

    self.clientId = self.mydata['clientId']
    self.privateKey = curve25519.Private(secret=keySecret)
    self.publicKey = self.privateKey.get_public()
    logging.info('ClientId %s' % self.clientId)
    logging.info('Exiting Initlocalparms')

    if self.sessionExists:
      self.setConnInfoParams(base64.b64decode(self.data["secret"]))

  def sendKeepAlive(self):
    message = "?,,"
    self.ws.send(message)
    logging.info(message)
    if self.keepAliveTimer is not None:
      self.keepAliveTimer.cancel()
    self.keepAliveTimer = Timer(15, lambda: self.sendKeepAlive())
    self.keepAliveTimer.start()

  def startSubscribeTimer(self):
    self.worker.subscribe()
    if self.subscribeTimer is not None:
      self.subscribeTimer.cancel()
    self.subscribeTimer = Timer(11*60*60, lambda: self.startSubscribeTimer())
    self.subscribeTimer.start()

  def saveSession(self, jsonObj):
    jsonObj['myData'] = self.mydata
    if self.sessionExists:
      for key, value in jsonObj.iteritems():
        self.data[key] = value
      jsonObj = self.data
    with open(settingsFile, 'w') as outfile:
      json.dump(jsonObj, outfile)

  def restoreSession(self):
    if (os.path.exists(settingsFile)):
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

  def handleBinaryMessage(self, message):
    checkSum = message[:32]
    hashHMAC = HmacSha256(self.macKey, message[32:])
    if hashHMAC != checkSum:
      logging.info("Invalid Checksum")
      return
    decryptedMessage = AESDecrypt(self.encKey, message[32:])
    processedData = whatsappReadBinary(decryptedMessage, True)
    logging.info("Actual Message: %s", processedData)
    self.worker.handleIfConversation(processedData)

  def sendTextMessage(self, number, text):
    message = "?,,"
    self.ws.send(message)
    logging.info("sending message %s to %s" % (text, number))
    messageId = "3EB0" + binascii.hexlify(os.urandom(8)).upper()
    logging.info("Message id %s" % messageId)
    messageTag = str(getTimestamp())
    messageParams = {"key": {"fromMe": True, "remoteJid": number + "@s.whatsapp.net", "id": messageId},
                     "messageTimestamp": getTimestamp(), "status": 1, "message": {"conversation": text}}
    msgData = ["action", {"type": "relay", "epoch": str(self.messageSentCount)},
               [["message", None, WAWebMessageInfo.encode(messageParams)]]]
    encryptedMessage = WhatsAppEncrypt(self.encKey, self.macKey, whatsappWriteBinary(msgData))
    payload = bytearray(messageId) + bytearray(",") + bytearray(to_bytes(WAMetrics.MESSAGE, 1)) + bytearray(
      [0x80]) + encryptedMessage
    self.messageSentCount = self.messageSentCount + 1
    logging.info("Calling websocket")
    self.ws.send(payload, websocket.ABNF.OPCODE_BINARY)

  def on_message(self, ws, message):
    try:
      messageSplit = message.split(",", 1)
      if len(messageSplit) == 1:
        logging.info(message)
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
            svgBuffer = io.BytesIO();  # from https://github.com/mnooner256/pyqrcode/issues/39#issuecomment-207621532
            img = pyqrcode.create(qrCodeContents, error='L')
            img.svg(svgBuffer, scale=6, background="rgba(0,0,0,0.0)", module_color="#122E31", quiet_zone=0)
            print(img.terminal(quiet_zone=1))
        elif isinstance(jsonObj, list) and len(jsonObj) > 0:
          if jsonObj[0] == "Conn":
            logging.info("Connection msg received")
            self.sendKeepAlive()
            if self.sessionExists is False:
              self.setConnInfoParams(base64.b64decode(jsonObj[1]["secret"]))
            self.saveSession(jsonObj[1])
            if self.subscribeStarted is False:
              self.startSubscribeTimer()
              self.subscribeStarted = True

          elif jsonObj[0] == "Cmd":
            logging.info("Challenge received")
            cmdInfo = jsonObj[1]
            if cmdInfo["type"] == "challenge":
              challenge = base64.b64decode(cmdInfo["challenge"])
              sign = base64.b64encode(HmacSha256(self.macKey, challenge))
              logging.info('sign %s' % sign)
              messageTag = str(getTimestamp())
              message = ('%s,["admin","challenge","%s","%s","%s"]' % (
                messageTag, sign, self.data["serverToken"], self.clientId))
              logging.info('message %s' % message)
              ws.send(message)
          elif jsonObj[0] == "Presence":
            self.worker.writePresenceToFilefromJson(jsonObj[1])
        elif isinstance(jsonObj, object):
          status = jsonObj["status"]

    except:
      logging.info("Some error encountered")
      raise

  def on_error(self, ws, error):
    logging.info(error)

  def on_close(self, ws):
    logging.info("### closed ###")

  def on_open(self, ws):
    logging.info("Socket Opened")
    logging.info("ClientId %s" % self.clientId)
    messageTag = str(getTimestamp())
    message = messageTag + ',["admin","init",[' + WHATSAPP_WEB_VERSION + '],["Chromium at ' + datetime.datetime.now().isoformat() + '","Chromium"],"' + self.clientId + '",true]'
    logging.info(message)
    ws.send(message)

    if self.data is not None:
      clientToken = self.data["clientToken"]
      serverToken = self.data["serverToken"]
      messageTag = str(getTimestamp())
      message = ('%s,["admin","login","%s","%s","%s","takeover"]' % (
        messageTag, clientToken, serverToken, self.clientId))
      logging.info(message)
      ws.send(message)
    else:
      logging.info("No data")

  def connect(self):
    self.initLocalParams()
    # websocket.enableTrace(True)
    self.ws = websocket.WebSocketApp("wss://web.whatsapp.com/ws",
                                     on_message=lambda ws, msg: self.on_message(ws, msg),
                                     on_error=lambda ws, msg: self.on_error(ws, msg),
                                     on_close=lambda ws: self.on_close(ws),
                                     on_open=lambda ws: self.on_open(ws),
                                     header={"Origin: https://web.whatsapp.com"})

    self.ws.run_forever()


if __name__ == "__main__":
  logging.basicConfig(filename=loggingDir + "/info.log",
                      format='[%(asctime)s] {%(filename)s:%(lineno)d} - %(message).300s', level=logging.INFO,
                      filemode='a')
  logging.Formatter.converter = customTime

  iworker = Worker(subscribeListFile, presenceFile)
  wa = WhatsApp(iworker)
  iworker.wa = wa
  wa.connect()
