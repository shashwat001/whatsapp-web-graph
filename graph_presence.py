from os.path import expanduser
from utilities import customTime
import logging
from datetime import datetime

import matplotlib
import matplotlib.pyplot as plt; plt.rcdefaults()
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from matplotlib.dates import HourLocator

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
            numberData[number]['timesum'] = datetime.strptime("0:00:01", "%H:%M:%S")
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

def sortData():
    ar = []
    for k,v in numberData.iteritems():
        ar.append((k, v['timesum']))
    ar = sorted(ar, key=lambda x: x[1])
    y_pos = []
    x_pos = []
    for l in ar:
        x_pos.append(l[0])
        y_pos.append(l[1])
    return x_pos, y_pos

def generateGraph():
    objects, performance = sortData()
    # objects = ('Python', 'C++', 'Java', 'Perl', 'Scala', 'Lisp')
    y_pos = np.arange(len(objects))
    # performance = [10,8,6,4,2,1]

    ax = plt.subplot()
    plt.barh(y_pos, performance, align='center', alpha=0.5)
    plt.yticks(y_pos, objects)
    plt.xlabel('Time')
    plt.title('User')
    ax.xaxis.set_major_locator(HourLocator())
    ax.xaxis.set_major_formatter(DateFormatter('%H:%M:%S'))
    plt.show()

def genSO():
    numbers, times = sortData()
    y = times
    ax = plt.subplot()
    ax.barh(numbers, y, align='center', alpha=0.5)
    ax.xaxis.set_major_locator(HourLocator())
    ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
    plt.show()

if __name__ == "__main__":
    logging.basicConfig(filename=loggingDir+"/graph.log",format='%(asctime)s - %(message).300s', level=logging.INFO, filemode='w')
    logging.Formatter.converter = customTime

    loadPresenceData()
    # sortData()
    
    
    # print(numberData)
    # generateGraph()
    genSO()
