#!/usr/bin/env python

# This script was written by David Bezdek for purpose of a master
# thesis: Torrent Peer Monitoring
# David Bezdek, xbezde11@stud.fit.vutbr.cz
# Faculty of Information Technology, Brno University of Technology
# 2018.05.23

# Support script for summarizing outputs from dht crawlers
# For running place the script to the same folder as outputs files 

import time
import os, sys
import fnmatch

class Evaluator(object):
    def __init__(self):
        self.files = self.getFiles()
        self.noFiles = len(self.files)
        
        self.noNodeSet = 0
        self.percentageResponse = 0
        self.percentageDuplResponse = 0
        
        self.noTorrents = 0
        self.noFoundPeers = 0
        self.noAllPeers = 0
        self.noAfterMergePeers = 0
        
        self.noFilteredPeers = 0
        self.noAfterFilterPeers = 0
        self.noAfterPing = 0
        pass
        
        
    def getFiles(self):
        files = []
        for file in os.listdir('.'):
            if fnmatch.fnmatch(file, "output*"):
                #print ("Loading File:", file)
                files.append(file)
        return files
    
    def getValue(self, info):
        return int(info.split(':')[1])
        
    def getPercentageValue(self, info):
        pom = info.split(':')[1]
        pom = pom[:(len(pom)-1)] # to remove char %
        return float(pom)
        
    def parseFirstLine(self, line):
        pom = line.split()
        #print pom
        self.noNodeSet += self.getValue(pom[0])
        self.percentageResponse += self.getPercentageValue(pom[1])
        self.percentageDuplResponse += self.getPercentageValue(pom[3])
        pass
        
    def parseLine(self, line):
        pom = info.split(':')[1]
        
        
    def readFiles(self):
        
        for output in self.files:
            f = open(output, 'r')
            lineCount = 0
            for line in f:
                #sys.stdout.write(line)
                if lineCount == 0:
                    self.parseFirstLine(line)
                elif lineCount == 1:
                    self.noFoundPeers += self.getValue(line)
                elif lineCount == 2:
                    self.noTorrents += self.getValue(line)
                elif lineCount == 3:
                    self.noAllPeers += self.getValue(line)
                elif lineCount == 4:
                    self.noAfterMergePeers += self.getValue(line)
                elif lineCount == 5:    
                    self.noFilteredPeers += self.getValue(line)
                elif lineCount == 6:
                    self.noAfterFilterPeers += self.getValue(line)
                elif lineCount == 7:
                    self.noAfterPing += self.getValue(line)
                lineCount += 1    

            f.close() 
        
        pass
    
    def printSummary(self):
        print "Total amount of nodes ------------------------: %i -- avrg: %i" % (self.noNodeSet, (self.noNodeSet/ self.noFiles))
        print "Average percentage of responses --------------: %.2f%%" % (self.percentageResponse / self.noFiles)
        print "Average percentage of duplicated nodes in resp: %.2f%%\n\n" % (self.percentageDuplResponse / self.noFiles)
        
        print "Peers:"
        print "Number of Torrents -------------- : %i" % self.noTorrents
        print "Number of Torrents without peers: : %i" % self.noFoundPeers
        print "Number of all reported peers ---- : %i  --- avrg: %i" % (self.noAllPeers, (self.noAllPeers/ self.noFiles))
        print "Number of After Merge peers ----- : %i" % self.noAfterMergePeers
        print "\t\t\t       ----"
        duplic = (self.noAllPeers - self.noAfterMergePeers )
        print "Number of duplication -------: %i  --- avrg: %i" % (duplic, (duplic/ self.noFiles))
        print "Percentage of duplication----: %.2f%%\n\n" % ((float(duplic)*100/ self.noAllPeers))
        
        print "Filter:"
        print "Number of filtered peers ----: %i" % self.noFilteredPeers
        print "Percentage of filtered peers-: %.2f%%\n\n" % (float(self.noFilteredPeers)*100 /  float(self.noAfterMergePeers))
        
        print "Ping:"
        print "Number of After Filter peers ------- : %i" % self.noAfterFilterPeers 
        print "Number of peers after ping --------- : %i" % self.noAfterPing
        print "Number of reduced peers via ping --- : %i" % (self.noAfterFilterPeers-self.noAfterPing)
        print "Percentage of reduced peers via ping : %.2f%%" % (float(self.noAfterFilterPeers-self.noAfterPing)*100 / float(self.noAfterFilterPeers))
        pass
    
if __name__ == '__main__':
    
    eval = Evaluator()
    eval.readFiles()

    if eval.noFiles != 0:
        eval.printSummary()

    pass