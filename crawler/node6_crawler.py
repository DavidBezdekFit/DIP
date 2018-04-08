#!/usr/bin/env python

import socket
import Queue
import time
import threading
import json
import fnmatch, re
import codecs
import io 
import os, sys

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
    def __init__(self, id = None):
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

        self.isock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.isock.bind( ("",self.port) )
        self.isock_lock = threading.Lock()

        pass
    
    def findNode6(self, host, port, target):
        mtid = 5
        msg = bencode({"t":chr(mtid), "y":"q", "q":"find_node", "a":  {"id":self.id, "target":target}, "want": ["n6"]})  
        #parameter "want": ["n6"] in find_node works, but IPv6 values still has to be sent over IPv6 socket
        # In other words - "n6" works for nodes, but not for "values" (reply of get_peers)
        self.isock.sendto(msg, (host,port))
        pass    
        
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
                if id != self.id:
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
                self.findNode(node["host"], node["port"], self.id)
                """if (distance(self.id, node["id"])>>148)==0:
                    #self.findNode(node["host"], node["port"], node["id"])
                    for i in range(1,5):
                        tid = stringify(intify(node["id"]) ^ (2**(i*3) - 1))
                        self.findNode(node["host"], node["port"], tid)
                
                # This threshold can be tuned, maybe use self.respondent
                #elif self.tn < 2000:
                elif len(self.nodePool) < 100000: 
                    self.findNode(node["host"], node["port"], self.id)
                    #for i in range(1,5):
                    #    self.findNode(node["host"], node["port"], newID())"""
            except Exception, err:
                #print("Unexpected error:", sys.exc_info()[0])
                print "Exception:Crawler.start_sender()", err, 
                print node
        pass
    
    def info(self):
        print "[NodeSet]:%i\t[12-bit Zone]:%i [%i/s]\t[Response]:%.2f%%\t[Queue]:%i\t[Dup]:%.2f%%" % \
              (len(self.nodePool), self.tn, self.tnspeed,
               self.respondent*100.0/max(1,len(self.nodePool)),
               self.nodeQueue.qsize(), self.duplicates*100.0/self.total)
        pass
    
    def convergeSpeed(self,node):
        if (distance(self.id, node["id"])>>148)==0:
            self.tn += 1
        if (time.time()-self.tntold) >= 5:
            self.tnspeed = int((self.tn-self.tnold)/(time.time()-self.tntold))
            self.tnold = self.tn
            self.tntold = time.time()
        pass
    
    
    #read some additional ipv6 address for better bootstraping
    def readNodes(self):
        try:
            for file in os.listdir('.'):
                if fnmatch.fnmatch(file, 'ipv6.*'):
                    print "Loading File:", file                
                    f = open(file, 'r')
                    text = f.read()
                    bla = json.loads(text)
                    
                    for key in bla:
                        node = {}
                        node = bla[key]
                        node["id"] = stringify(int(key)) 
                        
                        node["timestamp"] = time.time()
                        node["rtt"] = float('inf')
                        self.nodeQueue.put(node)
                    print len(bla)
        except Exception, err:
            pass
        pass
        
        
if __name__=="__main__":
    now = time.time()
    id = stringify(int(sys.argv[1])) if len(sys.argv)>1 else newID()
    crawler = NodeCrawler(id)
    # Try to load local node cache
    #crawler.readNodes()
      
    crawler.info()
    # Try to get bootstrap nodes from official router
     
    try:
        crawler.findNode("dht.transmissionbt.com", 6881, crawler.id) # reply on want n6 -- combination n4 and n6 no reply, 
    except:
        print "Can not connect to central dht.transmissionbt.com"
        pass
    try:
        crawler.findNode("router.silotis.us", 6881, crawler.id) 
    except:
        print "Can not connect to central router router.silotis.us"
        pass
              
    crawler.start_crawl(False)
    print "%.2f minutes" % ((time.time() - now)/60.0)
    crawler.serialize()
    pass 

    