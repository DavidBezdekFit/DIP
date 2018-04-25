#!/usr/bin/env python

# This script was written by David Bezdek for purpose of a master
# thesis: Torrent Peer Monitoring
# David Bezdek, xbezde11@stud.fit.vutbr.cz
# Faculty of Information Technology, Brno University of Technology
# 2018.05.23

# Small script for reading rss_feed file from parameters and for
# printing the average number of days of publishing the measured files

# how to run:
# python rss_age_finder.py -i rss_feed_unix.xml
# python rss_age_finder.py -i rss_feed_unix.xml -c 10
# python rss_age_finder.py -i rss_feed_unix.xml -c -10


import time
import os, sys
import xml.etree.ElementTree as ET
from datetime import date

imports_path = os.getcwd() + "/../imports/"
sys.path.append(imports_path) 
from db_utils import *

class AgeFinder(object):
    def __init__(self):
        self.tree = None
        self.dates = []
        self.calendar = {'Jan' : 1,'Feb' : 2,'Mar' : 3, 'Apr' : 4, 'May' : 5, 
        'Jun' : 6, 'Jul' : 7,'Aug' : 8, 'Sep' : 9, 'Oct' : 10, 'Nov':11, 'Dec' : 12} 
        pass
    
    def readFile(self, filename):
        try:
            f = open(filename, 'r')
            text = f.read()
            f.close()
        except:
            sys.stderr.write('Error in opening file: %s\n' % filename)
            sys.exit(-1)
        try:
            self.tree = ET.fromstring(text)
        except:
            sys.stderr.write('Invalid xml file')
            sys.exit(-1)
        pass
        
    #def getNum    
    
    def getFileInfo(self, item):
        try:
            pubDate =  item.find("pubDate").text
            pubDate = pubDate.split(' ')
            d0 = date(int(pubDate[3]), self.calendar[pubDate[2]], int(pubDate[1]))
            #today
            d1 = date(int(time.strftime("%Y")), int(time.strftime("%m")), int(time.strftime("%d")))
            delta = d1 - d0
            #print delta.days
            self.dates.append(delta.days)
        except Exception, err:
            print err
        pass
        
    def getItems(self):
        try: 
            xmlFile = self.tree.find("channel")
            for item in xmlFile:  
                if item.tag == "item":
                    self.getFileInfo(item)
        except:
            sys.stderr.write('Unexpected hierarchy in xml File\n')
            sys.exit(-1) 
        pass
    
    def getDates(self, num):
        #it counts from the end
        try:
            pomRange = abs(num)
        except:
            pomRange = len(self.dates)
            num = 0
        retDates = []
        if num < 0:
            maxindex = len(self.dates)-1
            for count in range(pomRange):
                retDates.append(self.dates[maxindex-count])
        else:
            for count in range(pomRange):
                retDates.append(self.dates[count])
        return retDates

    def getDateInfo(self, value):
        
        years = value/365
        print "years: %i" % years
        value = value - (years*365)
        #print "resting days: %i" % value
        months = value/30
        print "months: %i" % months
        value = value - (months*30)
        print "days: %i" % value
        return 
        
    def printDates(self, finDates):
        print finDates
        print "\nmax no. days: %i" % (max(finDates))
        find.getDateInfo(max(finDates))
        print "\nmin no. days: %i" % min(finDates)
        find.getDateInfo(min(finDates))
        avrg = sum(finDates)/len(finDates)
        print "\naverage no. days: %i" % (avrg)
        find.getDateInfo(avrg)
        pass
        
if __name__ == '__main__':
    
    
    if len(sys.argv) < 3:
        sys.stderr.write("You have to set the file via parameter -i")
        sys.exit(-1)
    params = getParam(sys.argv[1:])
    print params
    find = AgeFinder()
    filename = params['i']
    find.readFile(filename)
    find.getItems()
    #print find.dates
    
    finDates = find.getDates(params['c'])
    find.printDates(finDates)
    pass