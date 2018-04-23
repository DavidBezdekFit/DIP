#!/usr/bin/env python

# This script was written by David Bezdek for purpose of a master
# thesis: Torrent Peer Monitoring
# David Bezdek, xbezde11@stud.fit.vutbr.cz
# Faculty of Information Technology, Brno University of Technology
# 2018.05.23

# Support script for making an experiment for finding value p of 
# probability of missing node - searching injected nodes in found nodes

import os, sys
import fnmatch
import json

imports_path = os.getcwd() + "/../../DIP/imports/"
sys.path.append(imports_path) 

from khash import *
from db_utils import *

class Finder(object):
    def __init__(self):
        self.fileID = None
        self.nodePool = {}
        
        self.noAllNodes = 0
        self.noNbitNodes = 0
        pass
        
    def getID(self, filename):
        parts = filename.split('.')
        parts2 = parts[0].split('_')
        self.fileID = parts2[2]
        pass

    def getIDs(self):
        ids = []
        
        for file in os.listdir('.'):
            if fnmatch.fnmatch(file, 'injector_ids_*'):
                #print "nalezen file:", file
                f = open(file, "r")
                self.getID(file)
                for line in f.readlines():
                    #ids.append(stringify(long(line)))
                    ids.append(long(line))
        return ids
        
    def getFiles(self, folder):
        files = []
        for file in os.listdir('%i/' % folder):
            #print ("Loading File:", file)
            files.append(file)
        return files
    
    def getJsonData(self, folder, filename):
        try:
            path = "%s/" % folder
            path = path + filename
            f = open(path, 'r')
            text = f.read()
            dataJson = json.loads(text)
        except:
            print ("Error in reading file")
            raise
        return dataJson
    
    def readFiles(self, folder, files):
        for filename in files:
            print filename
            dataJson = self.getJsonData(folder, filename)
            self.noAllNodes += len(dataJson)
            
            count = 0
            for nodeid in dataJson:
                #print nodeid
                #print dataJson[nodeid]
                self.nodePool[long(nodeid)] = dataJson[nodeid]

            print "Number of diferent nodes:", len(self.nodePool)
            self.getNoNodesInZones()
        pass
    
    def getNoNodesInZones(self):
        pomID = long(self.fileID)
        oldLen = self.noNbitNodes  #for later minus
        for node in self.nodePool:
        
            if (distance(stringify(pomID), stringify(node))>>148)==0:
                self.noNbitNodes += 1
        self.noNbitNodes -=  oldLen
        print "Number of nodes in 12-bit zone: %i" % self.noNbitNodes
        pass
    
if __name__ == '__main__':
    

    
    finder = Finder()
    ids = finder.getIDs()

    
    #for id in ids:
    #    print id
    noExperiments = 5
    for i in range (1, noExperiments):
        
        files = finder.getFiles(i)       
        finder.readFiles(i, files)
       
        print "\n"
        #break
    
    
    noFound = 0
    print "\nfile ID: %s\n" % finder.fileID
    print "Finding"
    pomID = long(finder.fileID)
    noNbitNodes2 = 0
    for node in finder.nodePool:
        #print node
        if node in ids:
            print "shoda"
            print node
            
            noFound += 1

        if (distance(stringify(pomID), stringify(node))>>148)==0:
            noNbitNodes2 += 1
    print "Number of all nodes: %i" % finder.noAllNodes    
    print "Number of diferent nodes: %i" % len(finder.nodePool)
    
    
    print "Number of nodes in 12-bit zone: %i" % noNbitNodes2
    print "Number of nodes in 12-bit zone: %i" % finder.noNbitNodes
    print "Number of found: %i" % noFound
    
    
    
    #for id in ids:
        
    pass