#!/usr/bin/env python

# This script is experimental.
#
# Liang Wang @ Dept. Computer Science, University of Helsinki
# 2011.09.20
#

# This script was modified by David Bezdek for purpose of a master
# thesis: Torrent Peer Monitoring
# David Bezdek, xbezde11@stud.fit.vutbr.cz
# Faculty of Information Technology, Brno University of Technology
# 2018.05.23

import socket
import Queue
import time
import threading
import json
import os, sys
import fnmatch
import pickle
import logging

imports_path = os.getcwd() + "/../imports/"
sys.path.append(imports_path) 

from khash import *
from bencode import bencode, bdecode
from common import *
from db_utils import *
    
from abstract_crawler import AbstractCrawler

CTTIME = 10
PACKET_LEN = 1024


""" pro IPv6
    crawler.findNode("router.bittorrent.com", 6881, crawler.id)
    crawler.findNode("dht.transmissionbt.com", 6881, crawler.id)
    crawler.findNode("router.silotis.us", 6881, crawler.id)
    crawler.findNode("router.utorrent.com", 6881, crawler.id)
"""

class NodeCrawler(AbstractCrawler):
    def __init__(self, type, id = None):
        self.noisy = True                                       # Output extra info or not
        self.id = id if id else newID()                         # Injector's ID
        #self.ip = '2001:67c:1220:c1b1:4582:871a:2b8c:8088'
        self.port = get_port(30000, 31000)                      # my listening port
        self.nodePool = {}                                      # Dict of the nodes collected
        self.addrPool = {}                                      # Dict uses <ip,port> as its key
        self.nodeQueue = Queue.Queue(0)                         # Queue of the nodes to scan
        self.counter = CTTIME                                   # How long to wait after a queue is empty
        self.startTime = time.time()                            # Time start the crawler
        self.duplicates = 0                                     # How many duplicates among returned nodes
        self.total = 1                                          # Total number of returned nodes
        self.respondent = 0                                     # Number of respondent
        self.tn = 0                                             # Number of nodes in a specified n-bit zone
        self.tnold = 0
        self.tntold = 0
        self.tnspeed = 0

        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger()
        
        self.type = type if type else IPv4    
        if self.type == IPv4:
            self.isock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        else:
            self.isock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.my_bind("",self.port)
        self.isock_lock = threading.Lock()
        
        
        pass
        
    def serialize(self,timestamp):
        obj = {}
        for k, nlist in self.nodePool.items():
            for v in nlist:
                addr = (v['host'], v['port'])
                if addr in self.addrPool:
                    v["rtt"] = self.addrPool[addr]["timestamp"]- v["timestamp"]
                obj[k] = obj.get(k, []) + [v]
        self.logger.info("Serializing Nodes")    
        filename= "serializedIpv%snodes.%s.%s" % (str(self.type),timestamp, str(intify(self.id)))
        f = open(filename, "w")
        pickle.Pickler(f).dump(obj)
        f.close()
        pass
    
    def processNodes(self, nodes):
        timestamp = time.time()
        for node in nodes:
            id = node["id"]
            node["timestamp"] = timestamp
            node["rtt"] = float('inf')
            if id not in self.nodePool:
                self.nodePool[id] = [node]
                self.convergeSpeed(node)
                if id != self.id and len(self.nodePool) < 20000: # 100000 find 50/50
                    self.nodeQueue.put(node)
            else:
                if not self.hasNode(node["id"], node["host"], node["port"])\
                       and id != self.id:
                    self.nodePool[id].append(node)
                else:
                    self.duplicates += 1
            self.total += 1
        pass
    
    def start_sender(self, crawl):
        while self.counter:
            try:
                node = self.nodeQueue.get(True)
                if (distance(self.id, node["id"])>>148)==0:
                    self.findNode(node["host"], node["port"], node["id"])
                    for i in range(1,5):
                        tid = stringify(intify(node["id"]) ^ (2**(i*3) - 1))
                        self.findNode(node["host"], node["port"], tid)
                
                # This threshold can be tuned
                #elif self.tn < 2000:
                elif len(self.nodePool) < 100000: 
                    self.findNode(node["host"], node["port"], self.id)
            except Exception, err:
                self.logger.info( "Exception:Crawler.start_sender(): %s" % err )
        pass
    
    def info(self):
        self.logger.info( "[NodeSet]:%i\t[12-bit Zone]:%i [%i/s]\t[Response]:%.2f%%\t[Queue]:%i\t[Dup]:%.2f%%" % \
              (len(self.nodePool), self.tn, self.tnspeed,
               self.respondent*100.0/max(1,len(self.nodePool)),
               self.nodeQueue.qsize(), self.duplicates*100.0/self.total) )
        pass
    
    def convergeSpeed(self,node):
        if (distance(self.id, node["id"])>>148)==0:
            self.tn += 1
        if (time.time()-self.tntold) >= 5:
            self.tnspeed = int((self.tn-self.tnold)/(time.time()-self.tntold))
            self.tnold = self.tn
            self.tntold = time.time()
        pass
    
    
    #read some additional address for better bootstraping
    def loadCache(self):
        try:
            pomFile = "nodes%scache*" % str(self.type)
            for fileName in os.listdir('.'):
                if fnmatch.fnmatch(fileName, pomFile):
                    self.logger.info("Loading File: %s" % fileName)
                    #files.append(fileName)
                    f = open(fileName,"r")
                    nl = pickle.load(f)
                    for n in nl:
                        n["timestamp"] = time.time()
                        n["rtt"] = float('inf')
                        self.nodeQueue.put(n)
                    f.close()
                    """try:
                        os.remove(fileName)
                    except:
                        pass"""
        except:
            pass
        pass
        
        
if __name__=="__main__":
    now = time.time()
    
    params = getParam(sys.argv[1:])

    crawler = NodeCrawler(params['t'], params['id'])
    if params['v'] != None:
        crawler.logger.disabled = True
    # Try to load local node cache
    crawler.loadCache()
    
    crawler.logger.info( "queue size: %i" % crawler.nodeQueue.qsize())
    crawler.logger.info( "port: %i" % crawler.port)
    crawler.logger.info( "id: %s", str(intify(crawler.id))  )
    
    # Try to get bootstrap nodes from official router
    crawler.find_routers()

    crawler.start_crawl()
    crawler.logger.info( "%.2f minutes" % ((time.time() - now)/60.0))
    timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
    #crawler.serialize(timestamp)
    crawler.saveNodes(timestamp)
    pass 

    