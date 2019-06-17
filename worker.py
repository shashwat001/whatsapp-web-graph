import logging
from utilities import *

# ['action', {'add': 'relay'}, [{u'status': u'ERROR', u'message': {u'conversation': u'Test'}, u'key': {u'remoteJid': u'3456345@s.whatsapp.net', u'fromMe': False, u'id': u'62EC04FB60FFBD8A284C28E823EE2D5E'}, u'messageTimestamp': u'1560598969'}]]
class Worker:

    wa = None
    subscribeList = None
    subscriberList = set()

    def __init__(self, subscribeList):
        self.subscribeList = subscribeList

    def subscribe(self):
        logging.info("Subscribe list: %s" % self.subscribeList)
        try:
            lineList = None
            with open(self.subscribeList) as f:
                lineList = f.readlines()
            for line in lineList:
                self.subscriberList.add(line)
                self.sendSubscribe(str.strip(line))
        except:
            logging.info("Subscribe list not present")
            raise

    def addNewSubscribe(self, jid):
        number = self.getUserIdIfUser(jid)
        if number in self.subscriberList:
            return
        with open(self.subscribeList, "a+") as pFile:
            pFile.write('%s\n' % number)
        self.subscriberList.add(number)
        self.sendSubscribe(number)


    def sendSubscribe(self, userId):
        logging.info('Subsrcibing for %s' % userId)
        messageTag = str(getTimestampMs())
        message = ('%s,,["action", "presence", "subscribe", "%s@c.us"]' % (messageTag, userId))
        logging.info(message)
        self.wa.ws.send(message)

    def getUserIdIfUser(self, sender):
        jid = sender.split('@')[0]
        logging.info("Jid: %s" % jid)
        splitList = jid.split('-')
        if len(splitList) > 1:
            logging.info("Seems message from group: %s" % sender)
            raise ValueError("Sender seems a group")
        return splitList[0]

    def handleConversation(self, sender, message):
        userId = self.getUserIdIfUser(sender)
        logging.info("UserId: %s, Message:%s" % (userId, message))
        if message == "Add me":
            self.addNewSubscribe(sender)
            self.wa.sendTextMessage(userId, "Done")


        

    def handleIfConversation(self, messageJson):
        logging.info("Worker %s" % messageJson)
        if isinstance(messageJson, list) and len(messageJson) > 2:
            if messageJson[0] == 'action':
                metaData = messageJson[1]
                if (metaData is not None) and (isinstance(metaData, object)):
                    if 'add' not in metaData:
                        logging.info("Action untracked metadata %s" % metaData)
                    else:
                        if metaData['add'] != 'relay':
                            logging.info("Action untracked add metadata %s" % metaData['add'])
                        else:
                            actionJson = messageJson[2][0]
                            if 'key' not in actionJson:
                                logging.info('key not present in add relay')
                            else:
                                sender = actionJson['key']['remoteJid']
                                message = actionJson['message']['conversation']
                                self.handleConversation(sender, message)
                else:
                    logging.info("Action metadata not json: %s" % metaData)
            else:
                logging.info("Non tracked action: %s" % messageJson[0])
                logging.info("Value: %s" % messageJson[1])
                logging.info("ValueNext: %s" % messageJson[2])
