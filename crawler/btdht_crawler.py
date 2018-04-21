
import sys, os
import requests
import xml.etree.ElementTree as ET
import time
import threading
import btdht
import json

imports_path = os.getcwd() + "/../imports/"
sys.path.append(imports_path) 

from bencode import bencode, bdecode
from db_utils import *
from torrent_crawler import TorrentCrawler


def savePeers(peerPool):
    timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
    # make json file for peers
    
    print "Saving peers"
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
        print key
        #print stringify(int(key))
        #print obj[stringify(int(key))]
        if count > 5:
            break
        count += 1
    print len(bla)   
    print "peers file ok" """
    pass    

def setLimit(poolLen):
    if poolLen == 100: #JUST FOR TESTING - reducing size of files
        noSearchingFiles = 10
    else:
        noSearchingFiles = poolLen

    return noSearchingFiles

def wait(seconds): #wait for dht bootstrap
    print 'Waiting for bootstraping of dht'
    for pause in range (seconds/2):
        print ("waiting for boostraping...")
        time.sleep(2)
    pass

def start_crawl(filesPool):

    crawler = btdht.DHT()
    crawler.start()
    
    print crawler.myid.value
    #torrentID = crawler.myid.value 
    print "port:", crawler.bind_port
    
    noSearchingFiles = setLimit(len(filesPool))
    wait(10)

        
    print 'Start Finding'
    indexID = 1
    count = 0
    
    peerPool = {}
    noReportedPeers = 0
    
    noNoPeersFound = 0
    for item in filesPool:
        reportedPeers = crawler.get_peers(item[indexID])
        print "\n", item[0]
        print "reported peers:"
        print reportedPeers
        
        infohash = item[1].encode('hex').upper()
        #print infohash
        
        peers = []
        if reportedPeers == None:
            noNoPeersFound += 1
        else:
            noReportedPeers += len(reportedPeers)
            
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
    print ("Number of Seeking torrents -----------: %i" % noSearchingFiles  )
    print ("Number of torrents with no peers found: %i" % noNoPeersFound  )
    print ("Number of Reported peers -------------: %i" % noReportedPeers  )
    pass


if __name__=="__main__":
    
    torrent = TorrentCrawler()
    torrent.start_crawl(sys.argv[1:])
    
    start_crawl(torrent.filesPool)
    pass
    
    
