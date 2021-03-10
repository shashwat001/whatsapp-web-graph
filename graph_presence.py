#!/usr/bin/python

from os.path import expanduser
from utilities import *
import logging
from datetime import datetime, timedelta
from absl import flags
from absl import app

import matplotlib
import matplotlib.pyplot as plt

plt.rcdefaults()
import numpy as np
import matplotlib.pyplot as plt
from operator import itemgetter
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
flags.DEFINE_boolean('sum', False, 'Print total time online.')
flags.DEFINE_integer('graph_type', 1, 'Graph type to show.', short_name='g')

# Default offline delay below is manually observed value
flags.DEFINE_integer('offline_delay', 14, 'Delay in seconds after offline status is received from actual offline',
                     short_name='d')

home = expanduser("~")
settingsDir = home + "/.wweb"
loggingDir = "./logs"
presenceFile = settingsDir + '/presence.json'

FMT = '%Y-%m-%d %H:%M:%S'


class OnlineInfo:

  def __init__(self):
    self.number = None
    self.id = None
    self.firstOnlineTime = None
    self.lastOfflineTime = None
    self.totalOnline = 0
    self.currentOnlineTime = None
    self.onlineCount = 0


class Graph:
  timeAfter = None
  timeBefore = None
  offlineDelay = None
  printSum = False
  numberData = {}

  def __init__(self, timeAfter, timeBefore, offlineDelay, printSum):
    self.timeAfter = timeAfter
    self.timeBefore = timeBefore
    self.offlineDelay = offlineDelay
    self.printSum = printSum

  def onlineSessionComplete(self, numberObj):
    numberObj.lastOfflineTime = numberObj.lastOfflineTime - timedelta(seconds=self.offlineDelay)
    numberObj.onlineCount +=1
    tdelta = self.getTimeDifference(numberObj.lastOfflineTime, numberObj.firstOnlineTime)
    print("Number: %s, %s to %s, Difference: %s" % (
      (numberObj.number), (numberObj.firstOnlineTime), (numberObj.lastOfflineTime), tdelta))
    self.add_time_difference(numberObj.number, tdelta)

  def ongoingOnlineSession(self, numberObj):
    numberObj.onlineCount +=1
    print("Number: %s, Currently online from: %s, Difference: %s" %
          (numberObj.number, numberObj.currentOnlineTime,
           str(self.getTimeDifference(datetime.now(),numberObj.currentOnlineTime)).split(".")[0]))


  def add_time_difference(self, number, tdelta):
    self.numberData[number].totalOnline = self.numberData[number].totalOnline + tdelta


  def getTimeDifference(self, newTime, oldTime):
    tdelta = newTime - oldTime
    if tdelta < timedelta(0):
      return timedelta(0)
    return tdelta


  def loadPresenceData(self):
    with open(presenceFile) as f:
      lineList = f.readlines()
    for line in lineList:
      line = line.strip()
      info = line.split(",")
      number = info[0]
      pType = info[1]
      vTime = datetime.strptime(info[2], FMT)

      if (self.timeAfter is not None) and (vTime < self.timeAfter):
          continue

      if (self.timeBefore is not None) and (vTime > self.timeBefore):
          continue

      if pType == 'composing':
        continue
      if number not in self.numberData:
        onlineInfo = OnlineInfo()
        onlineInfo.number = number
        onlineInfo.id = info[3]
        onlineInfo.totalOnline = datetime.strptime("0:00:00", "%H:%M:%S")
        self.numberData[number] = onlineInfo

      numberObj = self.numberData[number]


      if pType == 'available':
        if numberObj.currentOnlineTime is None:
          numberObj.currentOnlineTime = vTime
        else:
          continue
        if numberObj.firstOnlineTime is None:
          numberObj.firstOnlineTime = vTime
        else:
          if numberObj.lastOfflineTime is not None:
            difference_last_offline = self.getTimeDifference(vTime, numberObj.lastOfflineTime)
            if difference_last_offline.seconds <= FLAGS.ignore_difference_sec:
              continue
            else:
              self.onlineSessionComplete(numberObj)
              numberObj.lastOfflineTime = None
              numberObj.firstOnlineTime = vTime

      elif pType == 'unavailable':
        if numberObj.currentOnlineTime is None:
          continue
        numberObj.lastOfflineTime = vTime
        numberObj.currentOnlineTime = None
      else:
        continue

    for k, v in self.numberData.iteritems():
      if v.lastOfflineTime is not None and v.firstOnlineTime is not None:
        self.onlineSessionComplete(v)
    for k, v in self.numberData.iteritems():
      if v.currentOnlineTime is not None:
        self.ongoingOnlineSession(v)

    if self.printSum:
      for k, v in iter(self.sort_dict(self.numberData, self.cmp_lastoffline_info)):
        output = "Number: %s, Time: %s" % (k, v.totalOnline.strftime("%H:%M:%S"))
        if v.currentOnlineTime is None:
          output += ", Last online: {}".format(v.lastOfflineTime)
        else:
          output += ", Last online: now"
        print(output)


  def sort_dict(self, dict, comparison_func):
    return sorted(dict.iteritems(), key=itemgetter(1),
                  cmp=comparison_func)

  def cmp_lastoffline_info(self, v1, v2):
    if v1.currentOnlineTime is None and v2.currentOnlineTime is None:
      if v1.lastOfflineTime is None:
        return 1
      if v2.lastOfflineTime is None:
        return -1
      if v1.lastOfflineTime < v2.lastOfflineTime:
        return -1
      return 1
    if v1.currentOnlineTime is not None:
      if v2.lastOfflineTime is None:
        return -1
      else:
        return 1
    if v2.currentOnlineTime is not None:
      if v1.lastOfflineTime is None:
        return 1
      else:
        return -1



  def sortData(self, key=None, labels=None):
    ar = []
    for k, v in self.numberData.iteritems():
      if FLAGS.usertype == "number":
        ar.append((k, key(v), labels(v)))
      else:
        ar.append((v.id, key(v), labels(v)))
    ar = sorted(ar, key=lambda x: x[1])
    y_pos = []
    x_pos = []
    timestring = []
    for l in ar:
      x_pos.append(l[0])
      y_pos.append(l[1])
      timestring.append(l[2])
    return x_pos, y_pos, timestring


  def generateGraph(self):
    people, times, timestring = self.sortData(key=lambda x: convertToSeconds(x.totalOnline),
                                              labels= lambda x: x.totalOnline.strftime("%H:%M:%S"))
    fig, ax = plt.subplots()

    # Example data
    # people = ('Tom', 'Dick', 'Harry', 'Slim', 'Jim')
    y_pos = np.arange(len(people))
    error = np.random.rand(len(people))

    ax.barh(y_pos, times, xerr=error, align='center')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(people)
    ax.get_xaxis().set_visible(False)

    for i, v in enumerate(times):
      ax.text(v + 3, i, timestring[i], color='blue')
    # ax.xaxis.set_major_locator(MinuteLocator())
    # ax.xaxis.set_major_formatter(DateFormatter('%H:%M:%S'))

    plt.show()

  def generateCountGraph(self):
    people, times, timestring = self.sortData(key=lambda x: x.onlineCount,
                                              labels= lambda x: x.onlineCount)
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

  timeAfter = None
  timeBefore = None

  if FLAGS.timeafter is not None:
    timeAfter = datetime.strptime(FLAGS.timeafter, FMT)
  if FLAGS.timebefore is not None:
    timeBefore = datetime.strptime(FLAGS.timebefore, FMT)

  g = Graph(timeAfter, timeBefore, FLAGS.offline_delay, FLAGS.sum)
  g.loadPresenceData()
  if not FLAGS.skip_graph:
    if FLAGS.graph_type is 1:
      g.generateGraph()
    if FLAGS.graph_type is 2:
      g.generateCountGraph()

if __name__ == "__main__":
   app.run(main)