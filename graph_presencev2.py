#!/usr/bin/python

from os.path import expanduser
from utilities import *
import logging
from datetime import datetime
from absl import flags
from absl import app

import matplotlib
import matplotlib.pyplot as plt;

plt.rcdefaults()
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from matplotlib.dates import MinuteLocator

FLAGS = flags.FLAGS

flags.DEFINE_string('usertype', "id", 'Type of name on y axis.')
flags.DEFINE_string('timeafter', None, 'Starttime for the graph.', short_name='a')
flags.DEFINE_string('timebefore', None, 'Endtime for the graph.', short_name='b')
flags.DEFINE_boolean('skip_graph', False, 'Whether to avoid graph pop up.',
                     short_name='s')
flags.DEFINE_integer('ignore_difference_sec', -1, 'Time difference to keep '
                                                 'online.', short_name='i')

home = expanduser("~")
settingsDir = home + "/.wweb"
loggingDir = "./logs"
presenceFile = settingsDir + '/presence.json'
numberData = {}


class OnlineInfo:

  def __init__(self):
    self.id = None
    self.firstOnlineTime = None
    self.lastOfflineTime = None
    self.totalOnline = 0
    self.isCurrentlyOnline = False


def adddiff(number, newTime, oldTime):
  tdelta = getTimeDifference(newTime, oldTime)
  print("Number: %s, Difference: %s" % (number, tdelta))
  add_time_difference(number, tdelta)


def add_time_difference(number, tdelta):
  numberData[number].totalOnline = numberData[number].totalOnline + tdelta


def getTimeDifference(newTime, oldTime):
  FMT = '%Y-%m-%d %H:%M:%S'
  tdelta = datetime.strptime(newTime, FMT) - datetime.strptime(oldTime, FMT)
  return tdelta


def loadPresenceData():
  with open(presenceFile) as f:
    lineList = f.readlines()
  for line in lineList:
    line = line.strip()
    info = line.split(",")
    number = info[0]
    pType = info[1]
    vTime = info[2]

    if (FLAGS.timeafter is not None) and (vTime < FLAGS.timeafter):
        continue

    if (FLAGS.timebefore is not None) and (vTime > FLAGS.timebefore):
        continue

    if pType == 'composing':
      continue
    if number not in numberData:
      onlineInfo = OnlineInfo()
      onlineInfo.id = info[3]
      onlineInfo.totalOnline = datetime.strptime("0:00:00", "%H:%M:%S")
      numberData[number] = onlineInfo

    numberObj = numberData[number]


    if pType == 'available':
      numberObj.isCurrentlyOnline = True
      if numberObj.firstOnlineTime is None:
        numberObj.firstOnlineTime = vTime
      else:
        if numberObj.lastOfflineTime is not None:
          difference_last_offline = getTimeDifference(vTime, numberObj.lastOfflineTime)
          if difference_last_offline.seconds <= FLAGS.ignore_difference_sec:
            continue
          else:
            adddiff(number, numberObj.lastOfflineTime, numberObj.firstOnlineTime)
            numberObj.lastOfflineTime = None
            numberObj.firstOnlineTime = vTime

    elif pType == 'unavailable':
      if numberObj.isCurrentlyOnline is False:
        continue
      numberObj.lastOfflineTime = vTime
      numberObj.isCurrentlyOnline = False
    else:
      continue

  for k, v in numberData.iteritems():
    if v.lastOfflineTime is not None and v.firstOnlineTime is not None:
      adddiff(k, v.lastOfflineTime, v.firstOnlineTime)

def sortData():
  ar = []
  for k, v in numberData.iteritems():
    if FLAGS.usertype == "number":
      ar.append((k, convertToSeconds(v.totalOnline), v.totalOnline.strftime("%H:%M:%S")))
    else:
      ar.append((v.id, convertToSeconds(v.totalOnline), v.totalOnline.strftime("%H:%M:%S")))
  ar = sorted(ar, key=lambda x: x[1])
  y_pos = []
  x_pos = []
  timestring = []
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
    ax.text(v + 3, i, timestring[i], color='blue')
  # ax.xaxis.set_major_locator(MinuteLocator())
  # ax.xaxis.set_major_formatter(DateFormatter('%H:%M:%S'))

  plt.show()


def main(argv):
  FLAGS(sys.argv)
  logging.basicConfig(filename=loggingDir + "/graph.log",
                      format='%(asctime)s - %(message).300s',
                      level=logging.INFO, filemode='w')
  logging.Formatter.converter = customTime
  print(FLAGS.usertype)
  print(FLAGS.timeafter)
  loadPresenceData()
  if not FLAGS.skip_graph:
    generateGraph()

if __name__ == "__main__":
   app.run(main)