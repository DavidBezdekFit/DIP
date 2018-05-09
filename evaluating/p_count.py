#!/usr/bin/env python

# This script was written by David Bezdek for purpose of a master
# thesis: Torrent Peer Monitoring
# David Bezdek, xbezde11@stud.fit.vutbr.cz
# Faculty of Information Technology, Brno University of Technology
# 2018.05.23

# Support script for counting:
#    - value p - probability 
#    - deviation (smerodatna odchylka)
# It reads outputs of script finder.py
# It could be extended to read all nodes files and merge it, but it would
# run really long
#

import os
import math

class Counter(object):
    def __init__(self):
    
        self.folders = []
        self.innerFolders = []
        self.noOutputs = 0
        self.amountOfFound = 0
        self.found = []
        self.avrg = 0
        self.dispersionSquare = 0
        pass

    def getFolders(self, protoc):
        for name in os.listdir("."):
            if os.path.isdir(name) and protoc in name:
                #print os.path.abspath(name)
                #print name
                self.folders.append(name)
        pass   
    
    def getInnerFolders(self,folder):
        path = folder + "/"
        for name in os.listdir(path):
            pom = path+name
            if os.path.isdir(pom):
                #print name
                self.innerFolders.append(pom+ "/")
        pass   
    
    def clearInnerFolder(self):
        self.innerFolders = []
        pass
        
    def getValue(self, line):
        line = line.split(' ')
        return int( line[len(line)-1] )
        
    def readOutputFiles(self):
        for path in self.innerFolders:
            for name in os.listdir(path):
                if 'output' in name:
                    filename = path + name
                    #print filename
                    f = open(filename, 'r')
                    lines = f.readlines()
                    #last line contains result
                    try:
                        value = self.getValue(lines[len(lines)-1]) 
                        self.found.append(value)
                        self.amountOfFound += value
                    except:
                        pass
                    self.noOutputs += 1  
                    f.close()
        pass
        
    def printResult(self):
        noInjectedNodes = 50
        print "pocet outputs : %i" % self.noOutputs
        print "pocet injected: %i" % (self.noOutputs*noInjectedNodes)
        print "vysledna suma : %i" % self.amountOfFound
        self.avrg = float(self.amountOfFound) / self.noOutputs
        print "Procento nalezenych: %.2f%%" % (float(self.amountOfFound)*100.0/(self.noOutputs*noInjectedNodes))
        print "Vysledne p: %.4f" % (float(self.amountOfFound)/(self.noOutputs*noInjectedNodes))
        pass
        
    def clearVariables(self):
        self.noOutputs = 0
        self.amountOfFound = 0
        self.found = []
        self.avrg = 0
        self.dispersionSquare = 0
        pass
        
    def countDeviation(self):
        for value in self.found:
            dispersion = self.avrg - value
            #print dispersion
            self.dispersionSquare += pow(dispersion,2)
        
        # deviation = smerodatna odchylka
        print "Smerodatna odchylka: %.2f" % math.sqrt( self.dispersionSquare / len(self.found))
        pass

if __name__ == '__main__':
    
    protoc = ["ipv4", "ipv6"]
    cnt = Counter()

    for prot in protoc:
        print prot
        cnt.getFolders(prot)
        for folder in cnt.folders:
            cnt.getInnerFolders(folder)
            cnt.readOutputFiles()
            cnt.clearInnerFolder()
            
        cnt.folders = []
        cnt.printResult()
        cnt.countDeviation()
        cnt.clearVariables()
        print ""

    pass