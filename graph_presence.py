from os.path import expanduser
from utilities import customTime
import logging
from datetime import datetime

home = expanduser("~")
settingsDir = home + "/.wweb"
loggingDir = "./logs"
presenceFile = settingsDir + '/presence.json'

numberData = {}

def printdiff(number, newTime):
    oldTime = numberData[number]['timeinfo']["atime"]
    FMT = '%Y-%m-%d %H:%M:%S'
    # print("Old time: %s" % oldTime)
    # print("New time: %s" % newTime)
    tdelta = datetime.strptime(newTime, FMT) - datetime.strptime(oldTime, FMT)
    print("Number: %s, Difference: %s" % (number,tdelta))
    numberData[number]['timesum'] = numberData[number]['timesum'] + tdelta

def loadPresenceData():
    with open(presenceFile) as f:
        lineList = f.readlines()
    for line in lineList:
        line = line.strip()
        info = line.split(",")
        number = info[0]
        pType = info[1]
        vTime = info[2]

        if pType == 'composing':
            continue
        if number not in numberData:
            numberData[number] = {}
            numberData[number]['timesum'] = datetime.strptime("0:00:00", "%H:%M:%S")
        if 'timeinfo' not in numberData[number]:
            if pType == 'unavailable':
                continue
            numberData[number]['timeinfo'] = {}
            numberData[number]['timeinfo']["atime"] = vTime
            # print("Added: %s %s" % (number,numberData[number]['timeinfo']))
        elif pType == 'unavailable':
            assert('atime' in numberData[number]['timeinfo'])
            printdiff(number, vTime)
            numberData[number].pop('timeinfo')
        else:
            continue

if __name__ == "__main__":
    logging.basicConfig(filename=loggingDir+"/graph.log",format='%(asctime)s - %(message).300s', level=logging.INFO, filemode='w')
    logging.Formatter.converter = customTime

    loadPresenceData()
    for k,v in numberData.iteritems():
        print("%s: %s" % (k, v['timesum']))
    # print(numberData)
