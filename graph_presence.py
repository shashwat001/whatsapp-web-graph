from os.path import expanduser
from utilities import *
import logging
from datetime import datetime
from absl import flags

import matplotlib
import matplotlib.pyplot as plt; plt.rcdefaults()
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from matplotlib.dates import MinuteLocator



FLAGS = flags.FLAGS

flags.DEFINE_string('usertype', "id", 'Type of name on y axis.')

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
            numberData[number]['id'] = info[3]
            numberData[number]['timesum'] = datetime.strptime("0:00:00", "%H:%M:%S")
        if 'timeinfo' not in numberData[number]:
            if pType == 'unavailable':
                continue
            numberData[number]['timeinfo'] = {}
            numberData[number]['timeinfo']["atime"] = vTime
        elif pType == 'unavailable':
            assert('atime' in numberData[number]['timeinfo'])
            printdiff(number, vTime)
            numberData[number].pop('timeinfo')
        else:
            continue

def sortData():
    ar = []
    for k,v in numberData.iteritems():
        if FLAGS.usertype == "number":
            ar.append((k, convertToSeconds(v['timesum']),v['timesum'].strftime("%H:%M:%S")))
        else:
            ar.append((v['id'], convertToSeconds(v['timesum']),v['timesum'].strftime("%H:%M:%S")))
    ar = sorted(ar, key=lambda x: x[1])
    y_pos = []
    x_pos = []
    timestring = []
    print(ar)
    for l in ar:
        x_pos.append(l[0])
        y_pos.append(l[1])
        timestring.append(l[2])
    return x_pos, y_pos, timestring

def generateGraph():
    people, times, timestring = sortData()
    fig, ax = plt.subplots()

    # Example data
    # people = ('Tom', 'Dick', 'Harry', 'Slim', 'Jim')
    y_pos = np.arange(len(people))
    error = np.random.rand(len(people))

    ax.barh(y_pos, times, xerr=error, align='center')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(people)
    ax.set_xlabel('Time Spent')
    ax.get_xaxis().set_visible(False)

    for i, v in enumerate(times):
        print(i)
        ax.text(v + 3, i, timestring[i], color='blue')
    # ax.xaxis.set_major_locator(MinuteLocator())
    # ax.xaxis.set_major_formatter(DateFormatter('%H:%M:%S'))

    plt.show()

if __name__ == "__main__":
    FLAGS(sys.argv)
    logging.basicConfig(filename=loggingDir+"/graph.log",format='%(asctime)s - %(message).300s', level=logging.INFO, filemode='w')
    logging.Formatter.converter = customTime
    print(FLAGS.usertype)

    loadPresenceData()
    # sortData()
    
    
    # print(numberData)
    generateGraph()
    # genSO()

