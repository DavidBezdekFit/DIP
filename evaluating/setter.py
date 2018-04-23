#!/usr/bin/env python

# This script was written by David Bezdek for purpose of a master
# thesis: Torrent Peer Monitoring
# David Bezdek, xbezde11@stud.fit.vutbr.cz
# Faculty of Information Technology, Brno University of Technology
# 2018.05.23

# Support script for making an experiment for finding value p of 
# probability of missing node 

import os, sys

imports_path = os.getcwd() + "/../imports/"
sys.path.append(imports_path) 

from khash import *
from db_utils import *

class Setter(object):
    def __init__(self, id):
        self.id = id
        self.injIDs = []
        self.crawlIDs = []
        pass

    
if __name__ == '__main__':
    
    id = stringify(long(sys.argv[1])) if len(sys.argv)>1 else newID()
    
    setter = Setter(id)
    
    nBitZone = 12
    noIDs = 50
    noCrawlers = 5
    setter.injIDs = generate_injector_ids(intify(setter.id), nBitZone, noIDs)
    setter.crawlIDs = generate_injector_ids(intify(setter.id), nBitZone, noCrawlers)
    
    path = os.path.dirname(os.path.abspath(__file__))
    index = path.rfind('/') + 1
    newpath = path[:index] + "zone_agents/"
    #print newpath
    
    
    filename = "injector_ids_%s.txt" % (str(intify(setter.id)))
    filepath = os.path.join(newpath, filename)
    
    print "creating file: %s\n" % filepath

    f = open(filepath, "w")
    for tid in setter.injIDs:
        i = intify(tid)
        f.write("%s\n" % str(i))
    f.close()

    print "Commands for experiment over IPv4:"
    print "python node_injector.py %s" % intify(setter.id)
    for crawlID in setter.crawlIDs:    
        print "python xnode_crawler.py --id %s -t 4" % intify(crawlID)
    
    print "\nCommands for experiment over IPv6:"
    print "python node_injector6.py %s" % intify(setter.id)
    for crawlID in setter.crawlIDs:
        print "python xnode_crawler.py --id %s -t 6" % intify(crawlID)

    pass