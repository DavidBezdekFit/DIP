#!/usr/bin/env python

# This Monitoring script was written by David Bezdek for purpose of a master
# thesis: Torrent Peer Monitoring
# David Bezdek, xbezde11@stud.fit.vutbr.cz
# Faculty of Information Technology, Brno University of Technology
# 2018.05.23

import sys, os
import requests
import xml.etree.ElementTree as ET
import time
import threading
import btdht
import json
import logging

imports_path = os.getcwd() + "/../imports/"
sys.path.append(imports_path) 

from bencode import bencode, bdecode
from db_utils import *
from torrent_crawler import TorrentCrawler


logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()


def savePeers(peerPool,timestamp):
    # make json file for peers
    logger.info( "Saving peers" )
    filename= "ipv4peers.%s.json" % timestamp
    with open(filename, "w") as f:
        f.write(json.dumps(peerPool, ensure_ascii=False))
    f.close()               
    pass    

def setLimit(poolLen):
    #if poolLen == 100: #JUST FOR TESTING - reducing size of files
    #    noSearchingFiles = 10
    #else:
    noSearchingFiles = poolLen
    return noSearchingFiles

def my_wait(seconds): #wait for dht bootstrap
    logger.info('Waiting for bootstraping of dht')
    for pause in range (seconds/2):
        logger.info("waiting for boostraping...")
        time.sleep(2)
    pass

def printRes(noSearchingFiles,noNoPeersFound,noReportedPeers,timestamp, timeWithCrawl,timeJustSearch):
    logger.info("Number of Seeking torrents -----------: %i" % noSearchingFiles  )
    logger.info("Number of torrents with no peers found: %i" % noNoPeersFound  )
    logger.info("Number of Reported peers -------------: %i" % noReportedPeers  )
    logger.info("\nTime of crawling and searching--------: %i sec" % timeWithCrawl  ) 
    logger.info("Avrg for 1 torrent -------------------: %.2f sec" % (float(timeWithCrawl)/noSearchingFiles)) 
    logger.info("Time just searching ------------------: %i sec" % timeJustSearch  )
    logger.info("Avrg searching time for 1 torrent ----: %.2f sec" % (float(timeJustSearch) /noSearchingFiles) )
    #logger.info("Number of peers after ping -----------: %i" % noPingedPeers  )
    f = open('output-btdht-%s' % timestamp, 'w')
    f.write("Number of Seeking torrents -----------: %i\n" % noSearchingFiles  )
    f.write("Number of torrents with no peers found: %i\n" % noNoPeersFound  )
    f.write("Number of Reported peers -------------: %i\n" % noReportedPeers  )
    f.write("\nTime of crawling and searching--------: %i sec" % timeWithCrawl  ) 
    f.write("Avrg for 1 torrent -------------------: %.2f sec" % (float(timeWithCrawl)/noSearchingFiles)) 
    f.write("Time just searching ------------------: %i sec" % timeJustSearch  )
    f.write("Avrg searching time for 1 torrent ----: %.2f sec" % (float(timeJustSearch) /noSearchingFiles) )
    
    f.close()
    pass

def start_finding(noSearchingFiles, filesPool, crawler):        
    logger.info("Start Finding")
    indexID = 1
    count = 0
    peerPool = {}
    noReportedPeers = 0
    noNoPeersFound = 0
    for item in filesPool:
        reportedPeers = crawler.get_peers(item[indexID])
        logger.info("\n%s" % item[0] )
        infohash = item[1].encode('hex').upper()
        
        peers = []
        if reportedPeers == None:
            noNoPeersFound += 1
        else:
            noReportedPeers += len(reportedPeers)
            logger.info("reported peers: %i" % len(reportedPeers))            
            #part for saving peers      
            peerTimestamp = time.time()
            for peer in reportedPeers:
                peers.append( { "addr" : peer, "timestamp" : peerTimestamp } )
            
        #this modul doesnt provide nodes that report peers - nodes are empty   
        peerPool[infohash] = { "name" : item[0], \
                              "nodes" : [], \
                              "peers" : peers }
   
        if count >= noSearchingFiles:
            break
        count += 1
    return peerPool, noNoPeersFound , noReportedPeers


def start_crawl(filesPool):

    crawler = btdht.DHT()
    crawler.start()
    
    #logger.info( crawler.myid.value )
    #torrentID = crawler.myid.value 
    logger.info("port: %i" % crawler.bind_port)
    
    now = time.time()
    noSearchingFiles = setLimit(len(filesPool))
    my_wait(18)
    
    now2 = time.time() 
    
    peerPool, noNoPeersFound , noReportedPeers = start_finding(noSearchingFiles, filesPool, crawler)

    crawler.stop()
    endtime = time.time()
    timeWithCrawl = endtime - now
    timeJustSearch = endtime - now2
    time.sleep(1)
    timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
    savePeers(peerPool,timestamp)
    printRes(noSearchingFiles,noNoPeersFound,noReportedPeers,timestamp, timeWithCrawl,timeJustSearch)

    pass


if __name__=="__main__":
    
    torrent = TorrentCrawler()

    params = getParam(sys.argv[1:])
    
    torrent.param = params
    torrent.start_crawl()

    if params['v'] != None:
        logger.disabled = True
    
    logger.info(params)
    start_crawl(torrent.filesPool)
    pass
    
    
