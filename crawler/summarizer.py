#!/usr/bin/env python

# This script was written by David Bezdek for purpose of a master
# thesis: Torrent Peer Monitoring
# David Bezdek, xbezde11@stud.fit.vutbr.cz
# Faculty of Information Technology, Brno University of Technology
# 2018.05.23

# Support script for summarizing outputs from dht crawlers
# 

import os, sys
import fnmatch
import json

IPv4 = 4
IPv6 = 6

class Summ(object):
    def __init__(self):
        self.btdhtPaths = []
        self.ipv4Paths = []
        self.ipv6Paths = []
        
        self.btdht_noMeasures = 0
        self.btdht_seekingTorrens = 0
        self.btdht_noPeersFound = 0
        self.btdht_reportedPeers = 0
        # list because time was not measured from start
        self.btdht_avrgSearchingTimeFor1Torr = [] 
        
        self.ipv4_nodeSet = 0
        self.ipv4_noMeasures = 0
        self.ipv4_seekingTorrents = 0
        self.ipv4_noPeersFound = 0
        self.ipv4_reportedPeers = 0
        self.ipv4_filteredPeers = 0
        self.ipv4_peersAfterFilter = 0
        self.ipv4_peersAfterPing = 0
        self.ipv4_runningTime = []
        self.ipv4_avrgSearchingTimeFor1Torr = []
        
        self.ipvType = 4
        pass
    
    def getFolders(self, noMeasure ):

        word = 'peers'
        for name in os.listdir("."):
            if os.path.isdir(name) and word in name:
                #print os.path.abspath(name)
                #print name
                folderPath1 = name + noMeasure
                for name2 in os.listdir(folderPath1):
                    pomPath = folderPath1+"/"+name2
                    if os.path.isdir(pomPath):
                        #print os.path.abspath(name2)
                        #print name2
                        if name2 == 'btdht':
                            self.btdhtPaths.append(pomPath)
                        elif name2 == 'ipv4':
                            self.ipv4Paths.append(pomPath)
                        elif name2 == 'ipv6':
                            self.ipv6Paths.append(pomPath)
        pass

    def getFilesInPath(self, path):
        files = []
        for name in os.listdir(path):
            
            if 'output' in name:
                #print name
                files.append(path+"/"+name)
        return files
        
    def getLineValue(self, line):
        line = line.split(' ')
        lastValue = line[len(line)-1]
        return int(lastValue)    
    
    def getTimeFor1Torrent(self, lines):
        lines = lines.split(' ')
        #print lines
        avrg = lines[len(lines)-2]
        self.btdht_avrgSearchingTimeFor1Torr.append( float(avrg) )    
        pass
     
    def readBtdhtData(self, outputs):
        for output in outputs:
            f = open(output, 'r')
            
            count = 0
            self.btdht_noMeasures += 1
            for line in f.readlines():
                #print line
                if count == 0:
                    self.btdht_seekingTorrens += self.getLineValue(line)
                elif count == 1:
                    self.btdht_noPeersFound += self.getLineValue(line)
                elif count == 2:
                    self.btdht_reportedPeers += self.getLineValue(line)
                #elif count == 3: just newline
                elif count == 4: # just newline
                    #print "line4"
                    self.getTimeFor1Torrent(line)
                    #
                count += 1
            f.close()
        pass
        
    def getNodeSet(self, line):
        line = line.split('\t')
        line = line[0].split(':')
        return int(line[1])
    
    def getTime(self, line):
        line = line.split(' ')
        return float(line[len(line)-2])
    
    def readIPv4Data(self, outputs):
        for output in outputs:
            f = open(output, 'r')
            #print output
            count = 0
            self.ipv4_noMeasures += 1
            for line in f.readlines():
                
                if count == 0:
                    self.ipv4_nodeSet += self.getNodeSet(line)
                elif count == 1:
                    self.ipv4_seekingTorrents += self.getLineValue(line)
                elif count == 2:
                    self.ipv4_noPeersFound += self.getLineValue(line)
                #elif count == 3: #reported peers before merge
                elif count == 4:
                    self.ipv4_reportedPeers += self.getLineValue(line)
                elif count == 5:
                    self.ipv4_filteredPeers += self.getLineValue(line)
                elif count == 6:
                    self.ipv4_peersAfterFilter += self.getLineValue(line)
                elif count == 7:
                    self.ipv4_peersAfterPing += self.getLineValue(line)
                    #"""
                #elif count == 8: #just new line 
                #elif count == 9: #time of running
                #elif count == 10: # avrg time on 1 torrent
                elif count == 11:  
                    self.ipv4_runningTime.append(self.getTime(line))
                elif count == 12:  
                    self.ipv4_avrgSearchingTimeFor1Torr.append(self.getTime(line))
                
                count += 1
            f.close()
            #break
        pass    
    
    def getBtdht(self,measure):
        
        for path in self.btdhtPaths:
            #print path
            outputs = self.getFilesInPath(path)
            self.readBtdhtData(outputs)
        
        print "\nBtdht measure: %s" % measure[1:]
        print "Number of measures --------: %i" % self.btdht_noMeasures
        print "Number of seeking torrents : %i" % self.btdht_seekingTorrens
        print "Number of no peers found --: %i" % self.btdht_noPeersFound 
        percentage1 = float(self.btdht_noPeersFound)*100 / float(self.btdht_seekingTorrens)
        print "Percentage of torrents with no peers find: %.2f%%" % percentage1
        print "\nNumber of reported peers --: %i" % self.btdht_reportedPeers
        
        # just without nopeersFound
        avrgOn1Torrent =  self.btdht_reportedPeers / (self.btdht_seekingTorrens-self.btdht_noPeersFound )
        print "Average of reported peers on 1 torrent (without no found): %i" % avrgOn1Torrent
        time = self.getSumTime(self.btdht_avrgSearchingTimeFor1Torr )
        print "Average running time for 1 Torrent  -----: %.2f" % (time / len(self.btdht_avrgSearchingTimeFor1Torr))
        #print self.btdht_avrgSearchingTimeFor1Torr    
        
        self.btdht_noMeasures = 0
        self.btdht_seekingTorrens = 0
        self.btdht_noPeersFound = 0
        self.btdht_reportedPeers = 0
        self.btdht_avrgSearchingTimeFor1Torr  = []
        pass
        
    
    def getSumTime(self, timelist):
        time = 0
        for timeIn in timelist:
            time += timeIn
        return time
    
    def printIpvInfo(self, measure):
        print "\nIPv%i measure: %s" % (self.ipvType, measure[1:])
        print "Number of measures --------: %i" % self.ipv4_noMeasures
        print "Number of nodes -----------: %i" % self.ipv4_nodeSet
        print "Number of seeking torrents : %i" % self.ipv4_seekingTorrents
        print "Number of no peers found --: %i" % self.ipv4_noPeersFound 
        percentage1 = float(self.ipv4_noPeersFound)*100 / float(self.ipv4_seekingTorrents)
        print "Percentage of torrents with no peers find: %.2f%%" % percentage1
        print "\nNumber of reported peers --: %i" % self.ipv4_reportedPeers
        avrgOn1Torrent = self.ipv4_reportedPeers/(self.ipv4_seekingTorrents-self.ipv4_noPeersFound )
        print "Average of reported peers on 1 torrent (without no found): %i" % avrgOn1Torrent
        print "Number of filtered peers --: %i" % self.ipv4_filteredPeers
        print "Number of peers after filter --: %i --- %.2f%%" % (self.ipv4_peersAfterFilter, (self.ipv4_peersAfterFilter*100.0 / self.ipv4_reportedPeers) )
        print "Number of peers after ping   --: %i ---- %.2f%%" % (self.ipv4_peersAfterPing,  (self.ipv4_peersAfterPing*100.0 / self.ipv4_peersAfterFilter) )

        time = self.getSumTime(self.ipv4_runningTime)
        print "Average running time   -----: %.2f" % (time / len(self.ipv4_runningTime))
        
        time = self.getSumTime(self.ipv4_avrgSearchingTimeFor1Torr)
        print "Average time for 1 torrent -: %.2f" % (time / len(self.ipv4_avrgSearchingTimeFor1Torr))
        
        self.clearIpv()
        pass
    
    def clearIpv(self):
        self.ipv4_nodeSet = 0
        self.ipv4_noMeasures = 0
        self.ipv4_seekingTorrents = 0
        self.ipv4_noPeersFound = 0
        self.ipv4_reportedPeers = 0
        self.ipv4_filteredPeers = 0
        self.ipv4_peersAfterFilter = 0
        self.ipv4_peersAfterPing = 0
        self.ipv4_runningTime = []
        self.ipv4_avrgSearchingTimeFor1Torr = []
        pass
    
    def getIpv4(self, measure):
        for path in self.ipv4Paths:
            #print path
            outputs = self.getFilesInPath(path)
            self.readIPv4Data(outputs)
        self.printIpvInfo( measure)
        self.ipv4Paths = []
        pass
    
    def getIpv6(self, measure):
        
        for path in self.ipv6Paths:
            #print path
            outputs = self.getFilesInPath(path)
            self.readIPv4Data(outputs)
        self.printIpvInfo( measure)
        self.ipv6Paths = []
        pass
    
if __name__ == '__main__':
  
    sum = Summ()

    measures = ["/1.mereni" , "/2.mereni" , "/3.mereni"]

    for measure in measures:
        print measure
        sum.getFolders(measure)

        sum.getBtdht(measure)
        sum.btdhtPaths = []
        
        """sum.ipvType = IPv4
        sum.getIpv4(measure)
        sum.ipv4Paths = []

        sum.ipvType = IPv6
        sum.getIpv6(measure)
        sum.ipv4Paths = []"""
        
        print ""
        #break
    pass
    