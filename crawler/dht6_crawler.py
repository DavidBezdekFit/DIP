#!/usr/bin/env python

import socket
import Queue
import time
import threading
import json
import abc
import errno
import os, sys

imports_path = os.getcwd() + "/../imports/"
sys.path.append(imports_path) 

from khash import *
from bencode import bencode, bdecode
from common import *
from db_utils import *
    
from abstract_crawler import AbstractCrawler
from torrent_crawler import TorrentCrawler

CTTIME = 3
PACKET_LEN = 1024

class DhtCrawler(AbstractCrawler):
    def __init__(self, id = None):
        self.noisy = True                                       # Output extra info or not
        self.id = id if id else newID()                         # Injector's ID
        #self.ip = '2001:67c:1220:c1b1:4582:871a:2b8c:8088'
        self.port = get_port(30000, 31000)                      # my listening port
        self.nodePool = {}                                      # Dict of the nodes collected
        self.nodePool_lock = threading.Lock()
        self.addrPool = {}                                      # Dict uses <ip,port> as its key
        self.nodeQueue = Queue.Queue(0)                         # Queue of the nodes to scan
        self.counter = CTTIME                                   # How long to wait after a queue is empty
        self.startTime = time.time()                            # Time start the crawler
        self.duplicates = 0                                     # How many duplicates among returned nodes
        self.total = 1                                          # Total number of returned nodes
        self.respondent = 0                                     # Number of respondent
        
        self.isock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.isock.bind( ("",self.port) )
        self.isock_lock = threading.Lock()
        
        self.filesPool = {}
        self.noSearchingFiles = 10                                #number of files from rss_feed.xml for that will be searched peers
        self.actualFile = ()      
        self.peerPool = {}
        self.peerReplied = []
        
        self.noENETUNREACH = 0
        self.noFiltered = 0
        self.noReportedPeers = 0
        pass
    
    def getFileName(self, infohash):
        result = ""
        for fileTuple in self.filesPool:
            pomHash = fileTuple[1].encode('hex').upper()
            if pomHash == infohash:
                result = fileTuple[0]
        return result
    
    def serialize(self):
        obj = {}
        for k, nlist in self.nodePool.items():
            for v in nlist:
                addr = (v['host'], v['port'])
                if addr in self.addrPool:
                    v["rtt"] = self.addrPool[addr]["timestamp"]- v["timestamp"]
                obj[k] = obj.get(k, []) + [v]
        timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")

        #store nodePool
        obj3 = {}
        for infohash in obj:
            for dict in obj[infohash]:
                lv_timestamp = dict["timestamp"]
                pomid = str(intify(infohash))
                host = dict['host']
                port = dict['port']
                obj3[pomid] = { "host" : host, "port" : port, "timestamp" : lv_timestamp } 
        print "Saving Nodes"    
        filename= "ipv6nodes.%s.%s.json" % (timestamp, str(intify(self.id)))
        with open(filename, "w") as f:
            f.write(json.dumps(obj3, ensure_ascii=False))
        f.close()    
        
        # make json file for peers as well
        obj = {}

        for infohash in self.peerPool:
            nodes = []
            for node in self.peerPool[infohash]["nodes"]:
                nodeID = str(intify(node["nodeID"]))
                nodeAddr = ( node["nodeAddr"][0] , node["nodeAddr"][1])
                nodeTimestamp = 0
                if addr in self.addrPool:
                    nodeTimestamp = self.addrPool[addr]["timestamp"]
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
    
    def getPeers(self, host, port, target):
        mtid = 7
        msg = bencode({"t":chr(mtid), "y":"q", "q":"get_peers", "a":  {"id":self.id, "info_hash":target}}) 
        self.isock.sendto(msg, (host,port))
        pass
    
    def start_sender(self, crawl):
        while self.counter:
            try:
                node = self.nodeQueue.get(True)
                self.findNode(node["host"], node["port"], node["id"])
                
                if crawl and self.nodeQueue.qsize() < 10000:
                    #self.findNode(node["host"], node["port"], node["id"])
                    count = 0
                    for torrent in self.filesPool:
                        infohash = torrent[1]
                        self.findNode(node["host"], node["port"], infohash)
                        if count >= self.noSearchingFiles:
                            break
                        count = count + 1
                #elif not crawl:
                #    self.findNode(node["host"], node["port"], node["id"])
                
            except Exception, err:
                if err.errno == errno.EADDRNOTAVAIL:
                    # errno.EADDRNOTAVAIL => 125
                    #[Errno 125] Cannot assign requested address => 'host': '::ffff:195.178.202.132' = IPv4-mapped IPv6 address
                    # maybe send request over IPv4 with "want" : ["n6"]
                    pass
                elif err.errno == errno.ENETUNREACH:
                    # [Errno 114] Network is unreachable
                    self.noENETUNREACH += 1
                    pass
                else:
                    print "Exception:Crawler.start_sender()", err
        pass
    
    

    def info(self):
        print "[NodeSet]:%i\t[Response]:%.2f%%\t[Queue]:%i\t[Dup]:%.2f%%" % \
              (len(self.nodePool),
               self.respondent*100.0/max(1,len(self.nodePool)),
               self.nodeQueue.qsize(), self.duplicates*100.0/self.total)  

    def processNodes(self, nodes):
        timestamp = time.time()
        for node in nodes:
            id = node["id"]
            node["timestamp"] = timestamp
            if id not in self.nodePool:
                with self.nodePool_lock:
                    self.nodePool[id] = [node]
                if id != self.id and len(self.nodePool) < 100000:
                    self.nodeQueue.put(node)
            else:
                if not self.hasNode(node["id"], node["host"], node["port"])\
                       and id != self.id:
                    with self.nodePool_lock:       
                        self.nodePool[id].append(node)
                else:
                    self.duplicates += 1
            self.total += 1
        pass

    def start_searching(self):
        self.counter = CTTIME
        t1 = threading.Thread(target=self.start_listener, args=("values",False,))
        t1.daemon = True
        t1.start()
        
        t2 = threading.Thread(target=self.start_sender, args=(False,))
        t2.daemon = True
        t2.start()
        
        self.start_finder()
        
        print "Waiting for the last answers"
        time.sleep(2)
        self.info()
        self.counter = 0
        pass
 
    def start_finder(self):
        print "\n\nStart finder"

        count = 0
        for torrent in self.filesPool:
            print torrent[0]
            self.actualFile = torrent
            infohash = torrent[1]
            torrentID = torrent[1].encode('hex').upper()
            self.peerPool[torrentID] = []
            
            closeNodes = self.getClosestNodes(infohash, 5)

            for node in closeNodes:
                #print node
                for nodeInfo in node[1]:
                    self.getPeers(nodeInfo["host"], nodeInfo["port"], infohash)
            if count >= self.noSearchingFiles:
                break
            count = count +1
            time.sleep(2.5)
        pass
    
    def getClosestNodes(self, infohash, K):
        if len(self.nodePool) == 0:
            raise RuntimeError, "Empty routing table!"

        # Sort by distance to the targeted infohash
        # and return the top K matches
        nodes = []
        with self.nodePool_lock:
            nodes = [(node_id, self.nodePool[node_id]) for node_id in self.nodePool]
            nodes.sort(key=lambda x: strxor(infohash, x[0]))
            if K > len(nodes):
                K = len(nodes) - 1
        return nodes[:K]
        
    def mergePeers(self):
        for info in self.peerPool:
            merge = []
            nodeID = []
            for peer in self.peerPool[info]:
                merge = list(set(merge + peer["peers"] ))
                nodeID.append( { "nodeID" : peer["nodeID"], "nodeAddr" :  peer["nodeAddr"] } )
            self.peerPool[info] = {}
            self.peerPool[info] = { "name" : self.getFileName(info), "peers" : merge, "nodes" : nodeID}
        pass
    
    def filter_peers(self):
        print "Soft filtering"
        for info in self.peerPool:
            #print "Name:", self.peerPool[info]["name"] 
            for peer in self.peerPool[info]["peers"]:
                if peer[1] == 1:
                    #print "==1 -> delete", peer
                    self.noFiltered += 1
                    self.peerPool[info]["peers"].remove(peer)
        pass    
            
    def ping_peers(self):
        self.counter = 5
        t1 = threading.Thread(target=self.ping_listener, args=())
        t1.daemon = True
        t1.start()    
        print "Checking nodes via ping"
        for info in self.peerPool:
            print "Name:", self.peerPool[info]["name"] 
            #print self.peerPool[info]
            for peer in self.peerPool[info]["peers"]:
                self.ping(peer[0], peer[1])
                #time.sleep(0.05)
            time.sleep(2.5)

            #intersection 
            intersect = list(set(self.peerPool[info]["peers"]) & set(self.peerReplied) )
            self.peerPool[info] = { "name" : self.peerPool[info]["name"], "peers" : intersect, "nodes" : self.peerPool[info]["nodes"]}           
            self.peerReplied = []
            
        self.counter = 0
        pass
    
    def ping_listener(self):
        while self.counter:
            try:
                msg, addr = self.isock.recvfrom(PACKET_LEN)
                decMsg = bdecode(msg)
                #print addr
                if decMsg['y'] == 'r':
                    addr2 = (addr[0], addr[1] )
                    self.peerReplied.append(addr2)
                    self.addrPool[addr2] = {"timestamp":time.time()}
                    self.respondent += 1
            except Exception, err:
                print "Exception:Crawler.ping_listener():", err
                
        pass
        
    
if __name__ == '__main__':
    
    now = time.time()
    
    torrent = TorrentCrawler()
    torrent.start_crawl(sys.argv[1:])
    
    crawler = DhtCrawler()
    crawler.filesPool = torrent.filesPool

    try:
        crawler.findNode("dht.transmissionbt.com", 6881, crawler.id) # reply on want n6 -- combination n4 and n6 no reply, 
        crawler.findNode("router.silotis.us", 6881, crawler.id)                                                    #sometimes it doesnt reply even on n6 
    except:
        try:
            crawler.findNode("router.silotis.us", 6881, crawler.id) 
        except:
            print "Central routers did not reply"
        pass
    # collect some nodes for start
    crawler.start_crawl(False) 
    # search with querying the closest nodes
    
    if not crawler.nodePool:
        print "No response from central routers"
        sys.exit(0)
    
    crawler.start_searching()
    
    # part for mergePeers and check if they are alive with ping
    crawler.mergePeers()    
    
    print "\n\nAfter Merge"    
    noReportedPeers = 0
    for info in crawler.peerPool:
        #print "Info Hash:", info
        print "Name:", crawler.peerPool[info]["name"]
        #print crawler.peerPool[info]
        print "Number of peers:", len(crawler.peerPool[info]["peers"])
        noReportedPeers += len(crawler.peerPool[info]["peers"])
    
    
    #ping or just filter these with port 1
    crawler.filter_peers()
    print "\n\nAfter Filtering" 
    crawler.ping_peers()
    print "\n\nAfter Ping" 
    noPingedPeers = 0
    for info in crawler.peerPool:
        #print "\nInfo Hash:", info
        print "Name:", crawler.peerPool[info]["name"]
        #print crawler.peerPool[info]
        print "Number of peers:", len(crawler.peerPool[info]["peers"])
        noPingedPeers += len(crawler.peerPool[info]["peers"])
        
    crawler.info()
    crawler.serialize()
    
    print ("Number of error noENETUNREACH: %i" % crawler.noENETUNREACH  )
    
    crawler.info()
    print ("Number of Seeking torrents -----------: %i" % crawler.noSearchingFiles  )
    print ("Number of Reported peers after merge -: %i" % noReportedPeers  )
    print ("Number of Filtered peers -------------: %i" % crawler.noFiltered  )
    print ("Number of peers after filter----------: %i" % (noReportedPeers - crawler.noFiltered ) )
    print ("Number of peers after ping -----------: %i" % noPingedPeers  )

    pass