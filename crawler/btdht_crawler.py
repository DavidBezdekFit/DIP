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

def savePeers(peerPool):
    timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
    # make json file for peers
    
    logger.info( "Saving peers" )
    filename= "ipv4peers.%s.json" % timestamp
    with open(filename, "w") as f:
        f.write(json.dumps(peerPool, ensure_ascii=False))
    f.close()               
    
    #check of json consistency
    """f = open(filename, 'r')
    text = f.read()
    #print text, "\n\n\n\n"
    
    bla = json.loads(text)
    
    count = 0
    for key in bla:
        logger.info(key)
        #print stringify(int(key))
        #print obj[stringify(int(key))]
        if count > 5:
            break
        count += 1
    logger.info(len(bla))
    logger.info("peers file ok")"""
    pass    

def setLimit(poolLen):
    if poolLen == 100: #JUST FOR TESTING - reducing size of files
        noSearchingFiles = 10
    else:
        noSearchingFiles = poolLen

    return noSearchingFiles

def my_wait(seconds): #wait for dht bootstrap
    logger.info('Waiting for bootstraping of dht')
    for pause in range (seconds/2):
        logger.info("waiting for boostraping...")
        time.sleep(2)
    pass

def start_crawl(filesPool):

    crawler = btdht.DHT()
    crawler.start()
    
    #logger.info( crawler.myid.value )
    #torrentID = crawler.myid.value 
    logger.info("port: %i" % crawler.bind_port)
    
    noSearchingFiles = setLimit(len(filesPool))
    my_wait(10)
        
    logger.info("Start Finding")
    indexID = 1
    count = 0
    
    peerPool = {}
    noReportedPeers = 0
    #noPingedPeers = 0
    noNoPeersFound = 0
    for item in filesPool:
        reportedPeers = crawler.get_peers(item[indexID])
        logger.info("\n%s" % item[0] )
        logger.info("reported peers:")
        logger.info(reportedPeers)
        
        infohash = item[1].encode('hex').upper()
        #print infohash
        
        peers = []
        if reportedPeers == None:
            noNoPeersFound += 1
        else:
            noReportedPeers += len(reportedPeers)
            #part for ping peers
            """ping_peers(reportedPeers)
            logger.info("peers that replied:")
            logger.info(peerReplied)        
            noPingedPeers += len(peerReplied)"""            
            
            
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
        
    crawler.stop()
    time.sleep(1)
    savePeers(peerPool)
    logger.info("Number of Seeking torrents -----------: %i" % noSearchingFiles  )
    logger.info("Number of torrents with no peers found: %i" % noNoPeersFound  )
    logger.info("Number of Reported peers -------------: %i" % noReportedPeers  )
    #logger.info("Number of peers after ping -----------: %i" % noPingedPeers  )
    pass


if __name__=="__main__":
    
    torrent = TorrentCrawler()

    params = getParam(sys.argv[1:])
    print params
    torrent.param = params
    torrent.start_crawl()
    #torrent.start_crawl(sys.argv[1:])
    if params['v'] != None:
        logger.disabled = True
    
    start_crawl(torrent.filesPool)
    pass
    
    
