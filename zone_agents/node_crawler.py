#!/usr/bin/env python

import socket
import Queue
import time
import threading
import json
import os, sys
import fnmatch
import pickle

imports_path = os.getcwd() + "/../imports/"
sys.path.append(imports_path) 

from khash import *
from bencode import bencode, bdecode
from common import *
from db_utils import *
    
from abstract_crawler import AbstractCrawler
#from node_injector import start_injectors

CTTIME = 10
PACKET_LEN = 1024
IPv4 = 4

class NodeCrawler(AbstractCrawler):
    def __init__(self, id = None):
        self.noisy = True                                       # Output extra info or not
        self.id = id if id else newID()                         # Injector's ID
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
        
        self.isock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.my_bind("",self.port )
        self.isock_lock = threading.Lock()
        pass
    
    def my_bind(self, str, port):
        while True:
            try:
                self.isock.bind( (str,self.port) )
                #print 'port %i is ok' % self.port
                break
            except socket.error:
                #print("Port %i is already in use" %  port)
                self.port += 1
                pass
            
        print "Chosen port:", self.port
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
                if id != self.id and len(self.nodePool) < 100000:
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
                # This threshold can be tuned, maybe use self.respondent
                #elif self.tn < 2000:
                elif len(self.nodePool) < 100000:    
                    self.findNode(node["host"], node["port"], self.id)
            except Exception, err:
                print "Exception:Crawler.start_sender()", err
        pass
    
    def info(self):
        print "[NodeSet]:%i\t\t[12-bit Zone]:%i [%i/s]\t\t[Response]:%.2f%%\t\t[Queue]:%i\t\t[Dup]:%.2f%%" % \
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
    
    def serialize(self,timestamp):
        obj = {}
        for k, nlist in self.nodePool.items():
            for v in nlist:
                addr = (v['host'], v['port'])
                if addr in self.addrPool:
                    v["rtt"] = self.addrPool[addr]["timestamp"]- v["timestamp"]
                obj[k] = obj.get(k, []) + [v]
        print "Serializing Nodes"    
        filename= "serializedIpv4nodes.%s.%s.json" % (timestamp, str(intify(self.id)))
        with open(filename, "w") as f:
            f.write(json.dumps(obj, ensure_ascii=False))
        f.close()  
        pass
    
    def loadCache(self):
        try:
            pomFile = "nodes4cache*"
            for fileName in os.listdir('.'):
                if fnmatch.fnmatch(fileName, pomFile):
                    print ("Loading File:", fileName)
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
    
    
    id = stringify(int(sys.argv[1])) if len(sys.argv)>1 else newID()
    crawler = NodeCrawler(id)
    
    print intify(crawler.id)  
    #print crawler.id
    print "calling inject"
    """tx = threading.Thread(target=start_injectors, args=(intify(crawler.id),))
    tx.daemon = True
    tx.start()"""
    
    # Try to load local node cache
    crawler.loadCache()
    print crawler.nodeQueue.qsize()
    # Try to get bootstrap nodes from official router
    crawler.findNode("router.bittorrent.com", 6881, crawler.id)
    
        
    
    
    crawler.start_crawl(True)
    print "%.2f minutes" % ((time.time() - now)/60.0)
    
    timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
    crawler.serialize(timestamp)
    crawler.saveNodes(timestamp, IPv4)
    pass
    