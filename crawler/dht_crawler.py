#!/usr/bin/env python

# This Monitoring class was written by David Bezdek for purpose of a master
# thesis: Torrent Peer Monitoring
# David Bezdek, xbezde11@stud.fit.vutbr.cz
# Faculty of Information Technology, Brno University of Technology
# 2018.05.23


import socket
import Queue
import time
import threading
import json
import abc
import errno
import os, sys
import logging


imports_path = os.getcwd() + "/../imports/"
sys.path.append(imports_path) 

from khash import *
from bencode import bencode, bdecode
from common import *
from db_utils import *
    
from abstract_crawler import AbstractCrawler
from torrent_crawler import TorrentCrawler
#from param_parser import ParamParser

CTTIME = 3
PACKET_LEN = 1024


class DhtCrawler(AbstractCrawler):
    def __init__(self, type, id = None):
        self.noisy = True                                       # Output extra info or not
        self.id = id if id else newID()                         # Injector's ID
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
        
        self.type = type if type else IPv4    
        if self.type == IPv4:
            self.isock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        else:
            self.isock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.isock.bind( ("",self.port) )
        self.isock_lock = threading.Lock()
        
        self.filesPool = {}
        self.noSearchingFiles = 100                                #number of files from rss_feed.xml for that will be searched peers
        self.actualFile = ()      
        self.peerPool = {}
        self.peerReplied = []
        self.noNoPeersFound = 0
        
        self.noENETUNREACH = 0
        self.noFiltered = 0
        self.noAllPeers = 0
        
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger()
        pass
    
    def getFileName(self, infohash):
        result = ""
        for fileTuple in self.filesPool:
            pomHash = fileTuple[1].encode('hex').upper()
            if pomHash == infohash:
                result = fileTuple[0]
        return result
    
    def savePeers(self,timestamp):
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
               
        self.logger.info("Saving peers")
        filename= "ipv%speers.%s.%s.json" % (str(self.type),timestamp, str(intify(self.id)))
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
                
                """if crawl and self.nodeQueue.qsize() < 10000:
                    #self.findNode(node["host"], node["port"], node["id"])
                    count = 0
                    for torrent in self.filesPool:
                        infohash = torrent[1]
                        self.findNode(node["host"], node["port"], infohash)
                        if count >= self.noSearchingFiles:
                            break
                        count = count + 1
                elif not crawl:
                    print "actual file infohash:", self.actualFile[1]
                    #self.getPeers(node["host"], node["port"], self.actualFile[1])"""
                
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
                    self.logger.info("Exception:Crawler.start_sender() %s" % err)
        pass
    
    

    def info(self):
        self.logger.info( "[NodeSet]:%i\t[Response]:%.2f%%\t[Queue]:%i\t[Dup]:%.2f%%" % \
              (len(self.nodePool),
               self.respondent*100.0/max(1,len(self.nodePool)),
               self.nodeQueue.qsize(), self.duplicates*100.0/self.total)  )

    def processNodes(self, nodes):
        timestamp = time.time()
        for node in nodes:
            id = node["id"]
            node["timestamp"] = timestamp
            if id not in self.nodePool:
                with self.nodePool_lock:
                    self.nodePool[id] = [node]
                if id != self.id and len(self.nodePool) < 50000: #100000: pro ipv6 byl dobry 5000
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
        t1 = threading.Thread(target=self.start_listener, args=("values",))
        t1.daemon = True
        t1.start()
        
        t2 = threading.Thread(target=self.start_sender, args=(False,))
        t2.daemon = True
        t2.start()
        
        self.start_finder()
        
        self.logger.info( "Waiting for the last answers")
        time.sleep(2)
        self.info()
        self.counter = 0
        pass
        
    def sendGetPeers(self, infohash):
        closeNodes = self.getClosestNodes(infohash, 5)
        for node in closeNodes:
            #print node
            for nodeInfo in node[1]:
                self.getPeers(nodeInfo["host"], nodeInfo["port"], infohash)
        pass
 
    def start_finder(self):
        self.logger.info( "\n\nStart finder")

        count = 0
        for torrent in self.filesPool:
            self.logger.info( torrent[0])
            self.actualFile = torrent
            infohash = torrent[1]
            torrentID = torrent[1].encode('hex').upper()
            self.peerPool[torrentID] = []
            
            for i in range(5):
                self.sendGetPeers(infohash)
                time.sleep(0.1)        

            #time.sleep(2.5)
            time.sleep(0.5)
            self.sendGetPeers(infohash)
            time.sleep(1)
            
            count = count +1
            if count >= self.noSearchingFiles:
                break
            
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
        self.logger.info( "Soft filtering" )
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
        noNoPeersFound = 0
        self.logger.info("Checking nodes via ping")
        for info in self.peerPool:
            self.logger.info("Name: %s" % self.peerPool[info]["name"] )
            #print self.peerPool[info]
            if len(self.peerPool[info]["peers"]) == 0:		
                noNoPeersFound += 1
            for peer in self.peerPool[info]["peers"]:
                self.ping(peer[0], peer[1])
                #time.sleep(0.05)
            if len(self.peerPool[info]["peers"]) > 0:
                time.sleep(2.5)

            #intersection 
            intersect = list(set(self.peerPool[info]["peers"]) & set(self.peerReplied) )
            self.peerPool[info] = { "name" : self.peerPool[info]["name"], "peers" : intersect, "nodes" : self.peerPool[info]["nodes"]}           
            self.peerReplied = []
            
        self.counter = 0
        return noNoPeersFound
    
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
                self.logger.info("Exception:Crawler.ping_listener(): %s" % err)    
        pass
        
        
    def getReportedPeers(self):
        self.mergePeers()   
        noReportedPeers = 0
        self.logger.info("\n\nAfter Merge")  
        for info in self.peerPool:
            #print "Info Hash:", info
            self.logger.info("Name: %s" % self.peerPool[info]["name"])
            #print self.peerPool[info]
            self.logger.info("Number of peers: %i" % len(self.peerPool[info]["peers"]))
            noReportedPeers += len(self.peerPool[info]["peers"])
        return noReportedPeers
    
    def getPingedPeers(self):
        self.noNoPeersFound = self.ping_peers()
        self.logger.info("\n\nAfter Ping")
        noPingedPeers = 0
        for info in self.peerPool:
            #print "\nInfo Hash:", info
            self.logger.info("Name: %s" % self.peerPool[info]["name"])
            #print self.peerPool[info]
            self.logger.info("Number of peers: %i" % len(self.peerPool[info]["peers"]))
            noPingedPeers += len(self.peerPool[info]["peers"])
        return noPingedPeers
    
    def printEvaluation(self, noReportedPeers, noPingedPeers):
        #self.logger.info("\n\nNumber of error noENETUNREACH: %i" % self.noENETUNREACH  )
        self.info()
        self.logger.info("Number of Seeking torrents -----------: %i" % (self.noSearchingFiles)  )
        self.logger.info("Number Torrents with no peers---------: %i" % self.noNoPeersFound  ) 
        self.logger.info("Number of Reported peers -------------: %i" % self.noAllPeers  )
        self.logger.info("Number of Reported peers after merge -: %i" % noReportedPeers  )
        self.logger.info("Number of Filtered peers -------------: %i" % self.noFiltered  )
        self.logger.info("Number of peers after filter----------: %i" % (noReportedPeers - self.noFiltered ) )
        self.logger.info("Number of peers after ping -----------: %i" % noPingedPeers  ) 
        pass
        
    def printEvaluationToFile(self, noReportedPeers, noPingedPeers, timestamp):
        f = open('output---%s.txt' % (timestamp), 'w')
       
        #f.write("Number of error noENETUNREACH: %i\n" % self.noENETUNREACH  )
        f.write( "[NodeSet]:%i\t[Response]:%.2f%%\t[Queue]:%i\t[Dup]:%.2f%%\n" % \
              (len(self.nodePool),
               self.respondent*100.0/max(1,len(self.nodePool)),
               self.nodeQueue.qsize(), self.duplicates*100.0/self.total)  )
        f.write("Number of Seeking torrents -----------: %i\n" % (self.noSearchingFiles)  )
        f.write("Number Torrents with no peers---------: %i\n" % self.noNoPeersFound  )
        f.write("Number of Reported peers -------------: %i\n" % self.noAllPeers  )
        f.write("Number of Reported peers after merge -: %i\n" % noReportedPeers  )
        f.write("Number of Filtered peers -------------: %i\n" % self.noFiltered  )
        f.write("Number of peers after filter----------: %i\n" % (noReportedPeers - self.noFiltered ) )
        f.write("Number of peers after ping -----------: %i\n" % noPingedPeers  ) 
        f.close() 
        pass
    
if __name__ == '__main__':
    
    now = time.time()

    params = getParam(sys.argv[1:])
    
    torrent = TorrentCrawler()
    #torrent.param = parser.param
    torrent.param = params
    torrent.start_crawl()
    
    crawler = DhtCrawler(params['t'])
    
    # switching off the outputs
    if params['v'] != None:
        crawler.logger.disabled = True

    crawler.logger.info("type: IPv%s" % crawler.type)
    crawler.filesPool = torrent.filesPool
    if len(crawler.filesPool) == 100: #JUST FOR TESTING - reducing size of files
        crawler.noSearchingFiles = 10
    else:
        crawler.noSearchingFiles = len(crawler.filesPool)

    # bootstrap around 100 000 nodes to start
    crawler.start_crawl() 
    if not crawler.nodePool:
        crawler.logger.info("No response from central routers")
        sys.exit(0)
    
    crawler.start_searching() 
    
    noReportedPeers = crawler.getReportedPeers()
    #filter these with port 1
    crawler.filter_peers()
    
    timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
    try:
        crawler.savePeers(timestamp)
    except:
        sys.stderr.write('\nCant write peers into JSON, probably name of some torrent file is unsupported!\n\n')

    noPingedPeers = crawler.getPingedPeers()
    crawler.info()
    crawler.saveNodes(timestamp)
    crawler.printEvaluation( noReportedPeers, noPingedPeers )
    crawler.printEvaluationToFile( noReportedPeers, noPingedPeers, timestamp )

    pass