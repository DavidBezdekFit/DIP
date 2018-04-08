#
#
#
# this version using btdht library and try to ping reported peers
#   but they usualy dont reply back :( 
#   so this version is useless


import sys, os
import requests
import xml.etree.ElementTree as ET
import time
import threading
import btdht

imports_path = os.getcwd() + "/../imports/"
sys.path.append(imports_path) 

from bencode import bencode, bdecode
from db_utils import *
from torrent_crawler import TorrentCrawler


port = get_port(30000, 31000)
isock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
isock.bind( ("",port) )
addrPool = {}
peerReplied = []
torrentID = 0
runListening = False

def savePeers(peers):
    timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
    # make json file for peers
    obj = {}

    for infohash in self.peerPool:
        nodes = []
        for node in self.peerPool[infohash]["nodes"]:
            nodeID = str(intify(node["nodeID"]))
            nodeAddr = ( node["nodeAddr"][0] , node["nodeAddr"][1])
            nodeTimestamp = 0
            if nodeAddr in self.addrPool:
                nodeTimestamp = self.addrPool[nodeAddr]["timestamp"]
            nodes.append( { "nodeID" : nodeID, "nodeAddr" : nodeAddr, "timestamp" : nodeTimestamp} )    
        peers = []    
        for peer in self.peerPool[infohash]["peers"]:
            peerTimestamp = 0
            if peer in self.addrPool:
                peerTimestamp = self.addrPool[peer]["timestamp"]
            peers.append( { "addr" : peer, "timestamp" : peerTimestamp } )
            
        obj[infohash] = { "name" : self.peerPool[infohash]["name"], \
                          "nodes" : nodes, \
                          "peers" : peers }
           
    print "Saving peers"
    filename= "ipv6peers.%s.%s.json" % (timestamp, str(intify(self.id)))
    with open(filename, "w") as f:
        f.write(json.dumps(obj, ensure_ascii=False))
    f.close()               
    pass    
    
def ping(host, port):
        mtid = 3
        msg = bencode({"t":chr(mtid), "y":"q", "q":"ping", "a":  {"id":torrentID}})
        isock.sendto(msg, (host,port))
        pass
    
def ping_peers(peers):
    runListening = True
    t1 = threading.Thread(target=ping_listener, args=())
    t1.daemon = True
    t1.start()    
    print "Checking nodes via ping"
    for peer in peers:
        ping(peer[0], peer[1])
          
    time.sleep(2.5)  
    
    #it will stop the listener
    runListening = False
    
    #intersection 
    #intersect = list(set(peers) & set(self.peerReplied) )
    #self.peerPool[info] = { "name" : self.peerPool[info]["name"], "peers" : intersect, "nodes" : self.peerPool[info]["nodes"]}           
    #self.peerReplied = []
      
    pass

def ping_listener():
    while runListening:
        try:
            msg, addr = isock.recvfrom(PACKET_LEN)
            decMsg = bdecode(msg)
            #print addr
            if decMsg['y'] == 'r':
                print "Reply by:", addr
                peerReplied.append(addr)
                addrPool[addr] = {"timestamp":time.time()}
        except Exception, err:
            print "Exception:Crawler.ping_listener():", err
            
    pass

if __name__=="__main__":
    
    torrent = TorrentCrawler()
    torrent.start_crawl(sys.argv[1:])
    

    if len(torrent.filesPool) == 100: #JUST FOR TESTING - reducing size of files
        noSearchingFiles = 10
    else:
        noSearchingFiles = len(torrent.filesPool)
    
    crawler = btdht.DHT()
    crawler.start()
    print crawler.myid.value
    torrentID = crawler.myid.value
    print intify(crawler.myid.value)
    #print stringify(crawler.myid.value)
    #wait for dht bootstrap
    print 'Waiting for bootstraping of dht'
    for pause in range (12):
        print ("waiting for boostraping...")
        time.sleep(1)
        
    print 'Start Finding'
    indexID = 1
    count = 0
    print crawler.bind_port
    #crawler.sock.settimeout(2)
    
    peerPool = {}
    noReportedPeers = 0
    noPingedPeers = 0
    noNoPeersFound = 0
    for item in torrent.filesPool:
        reportedPeers = crawler.get_peers(item[indexID])
        print item[0]
        print "reported peers:"
        print reportedPeers
        
        infohash = item[1].encode('hex').upper()
        #print infohash
        
        if reportedPeers == None:
            noNoPeersFound += 1
        else:
            noReportedPeers += len(reportedPeers)
            #place for ping peers
            ping_peers(reportedPeers)
            print ("peers that replied:")
            print peerReplied        
            noPingedPeers += len(peerReplied)
        #part for saving peers
        """peers = []    
        for peer in reportedPeers:
            peerTimestamp = 0
            if peer in addrPool:
                peerTimestamp = addrPool[peer]["timestamp"]
            peers.append( { "addr" : peer, "timestamp" : peerTimestamp } )
            
        peerPool[infohash] = { "name" : item[0], \
                              "nodes" : [], \  #this modul doesnt provide nodes that report peers
                              "peers" : peers }
        
        print peers"""
   
        if count >= noSearchingFiles:
            break
        count += 1
    crawler.stop()
    time.sleep(1)
    print ("Number of Seeking torrents -----------: %i" % noSearchingFiles  )
    print ("Number of torrents with no peers found: %i" % noNoPeersFound  )
    print ("Number of Reported peers after merge -: %i" % noReportedPeers  )
    print ("Number of peers after ping -----------: %i" % noPingedPeers  )
    pass
    
    
