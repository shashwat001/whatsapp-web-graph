import logging

# ['action', {'add': 'relay'}, [{u'status': u'ERROR', u'message': {u'conversation': u'Test'}, u'key': {u'remoteJid': u'919472458688@s.whatsapp.net', u'fromMe': False, u'id': u'62EC04FB60FFBD8A284C28E823EE2D5E'}, u'messageTimestamp': u'1560598969'}]]
class Worker:

    def __init__(self):
        a = None

    def handleConversation(self, sender, message):
        jid = sender.split('@')[0]
        logging.info("Jid: %s" % jid)
        userId = jid.split('-')
        if len(userId) > 0:
            logging.info("Seems message from group: %s" % sender)
            return
        logging.info("Sender userid: %s" % userId)

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