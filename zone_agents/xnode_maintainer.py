#!/usr/bin/env python

# 
# This script is experimental.
#
# Liang Wang @ Dept. Computer Science, University of Helsinki
# 2011.09.21
#
# Rewriting the script by David Bezdek, 
#   xbezde11@stud.fit.vutbr.cz
#

import os, sys
import socket
import pickle
import random
import Queue
import time
import threading
import resource

imports_path = os.getcwd() + "/../imports/"
sys.path.append(imports_path) 

from khash import *
from bencode import bencode, bdecode
from common import *

from db_utils import *
from abstract_crawler import AbstractCrawler

MYPORT = 6886             # The port used for communication
ACTIVE_THRESHOLD = 10000   # The minimum number of nodes in nodePool
REFRESH_LIMIT = 60        # The time interval to refresh a node

TID = 't'
REQ = 'q'
RSP = 'r'
TYP = 'y'
ARG = 'a'
ERR = 'e'


#class Maintainer(object):
class Maintainer(AbstractCrawler):
    def __init__(self, type, id = None):
        self.id = id if id else newID()                         # Maintainer's ID
        self.noisy = True                                       # Output extra info or not
        self.nodePool = {}                                      # Dict of the nodes collected
        self.nodePool_lock = threading.Lock()
        self.nodeQueue = Queue.Queue(0)                         # Queue of the nodes to scan
        self.startTime = time.time()                            # Time start the crawler
        self.respondent = 0                                     # Number of respondent
        self.noCaches = 0
    
        self.type = type if type else IPv4
        if self.type == IPv4:
            self.isock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        else:
            self.isock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.isock.bind( ("",MYPORT) )
        self.isock_lock = threading.Lock()

        pass


    def addNode(self, node, ip):
        self.nodePool_lock.acquire()
        try:
            now = time.time()
            # Generate Ip pool
            IPs = [ x["host"] for x in self.nodePool.values() ]
            if node["id"] not in self.nodePool:
                if ip not in IPs:
                    node["timestamp"] = now
                    node["lastupdate"] = now - REFRESH_LIMIT
                    self.nodePool[node['id']] = node
            else:
                node = self.nodePool[node['id']]
                # only update the lastupdate if the message is from node itself
                if ip==node["host"]:
                    node["lastupdate"] = now
                    self.nodePool[node['id']] = node
        except Exception, err:
            print "Exception:Maintainer.addNode()", err
        self.nodePool_lock.release()
        pass

    def bootstrap(self):
        """Whenever the number of nodes in nodePool drops below the threshold,
        use this function to get more nodes."""
        self.nodePool_lock.acquire()
        try:
            if len(self.nodePool) == 0:
                self.find_routers()
                """try:
                    self.findNode("dht.transmissionbt.com", 6881, self.id) # reply on want n6 -- combination n4 and n6 no reply, 
                except:
                    print "Can not connect to central dht.transmissionbt.com"
                    pass
                try:
                    self.findNode("router.silotis.us", 6881, self.id) 
                except:
                    print "Can not connect to central router router.silotis.us"
                    pass"""
            else:
                for n in self.nodePool.values():
                    self.findNode(n["host"], n["port"], newID(), n["id"])
        except Exception, err:
            print "Exception:Maintainer.bootstrap()", err
        self.nodePool_lock.release()
        pass

    def findNode(self, host, port, target, rID = None):
        mtid = 5
        msg = bencode({"t":chr(mtid), "y":"q", "q":"find_node", "a":  {"id":self.id, "target":target}})
        
        self.sendMsg(msg, (host,port))
        pass
        
    def ping(self, host, port):
        mtid = 3
        msg = bencode({"t":chr(mtid), "y":"q", "q":"ping", "a":  {"id":self.id}})
        
        self.sendMsg(msg, (host,port))
        pass

    def pingNodes(self, nodes):
        for node in nodes:
            try:
                self.ping(node['host'], node['port'])
            except Exception, err:
                print "Exception:Maintainer.pingNodes():", err
        pass

    def processNodes(self, nodes):
        timestamp = time.time()
        for node in nodes:
            id = node["id"]
            if id not in self.nodePool:
                if id != self.id:
                    self.nodeQueue.put(node)
            self.addNode(node, node["host"])
        pass

    def scan_nodePool(self):
        """Kick out the dead nodes"""
        print "scan the nodePool"
        now = time.time()
        self.nodePool_lock.acquire()
        for n in self.nodePool.values():
            try:
                t = now - n["lastupdate"]
                if t >= REFRESH_LIMIT and t < 2*REFRESH_LIMIT:
                    self.ping(n["host"], n["port"])
                elif t >= 2*REFRESH_LIMIT:
                    self.nodePool.pop(n["id"])
                    print "kick out %s:%i" % (n["host"], n["port"])
            except Exception, err:
                print "Exception:Maintainer.scan_nodePool():", err, n
        self.nodePool_lock.release()
        pass

    def sendMsg(self, msg, addr):
        self.isock_lock.acquire()
        try:
            self.isock.sendto(msg, addr)
        except:
            pass
        self.isock_lock.release()
        pass

    def serialize(self):
        tmp = []
        obj = []
        self.nodePool_lock.acquire()
        try:
            # Choose those stable nodes to cache
            tmp = self.nodePool.values()
            tmp.sort(key=lambda x: x["timestamp"])
            tmp = tmp[:1000]
            #tmp = random.sample(tmp, min(100,len(tmp)))
            # Cache the nodes
            obj = []
            for v in tmp:
                try:
                    n = {}
                    n["id"] = v["id"]
                    n["host"] = v["host"]
                    n["port"] = v["port"]
                    n["timestamp"] = v["timestamp"]
                    n["lastupdate"] = v["lastupdate"]
                    obj.append(n)
                except Exception, err:
                    print "Exception:Maintainer.serialize():loop:", err
        except Exception, err:
            print "Exception:Maintainer.serialize():", err
        self.nodePool_lock.release()
        try:
            print "longest", time.time()-tmp[0]["timestamp"]
        except:
            pass
        print "writing into cache%s file" % str(self.noCaches)
        f = open("nodes%scache%s" % (str(self.type), str(self.noCaches)), "w")
        pickle.Pickler(f).dump(obj)
        f.close()
        self.noCaches += 1
        pass

    
    def start_listener(self):
        while True:
            try:
                msg, addr = self.isock.recvfrom(PACKET_LEN)
                #print 'listener accepted message'
                decMsg = bdecode(msg)
                msgTID = decMsg['t']
                msgType = decMsg['y']
                msgContent = decMsg[decMsg['y']]
                
                if msgType==RSP and "nodes" in msgContent:
                    if len(self.nodePool) < 2*ACTIVE_THRESHOLD:
                        self.processNodes(unpackNodes(msgContent["nodes"]))                
                if msgType==RSP and "nodes6" in msgContent:
                    if len(self.nodePool) < 2*ACTIVE_THRESHOLD:
                        self.processNodes(unpackIPv6Nodes(msgContent["nodes6"]))
                if msgType==RSP and "id" in msgContent:
                    id = msgContent["id"]
                    if id != self.id:
                        if id in self.nodePool or len(self.nodePool) < 2*ACTIVE_THRESHOLD:
                            self.addNode( {"id":id, "host":addr[0], "port":addr[1]}, addr[0] )
                self.respondent += 1
            except Exception, err:
                print "Exception:Maintainer.listener():", err
        pass

    def start_sender(self):
        while True:
            try:
                # Check are there any nodes in the queue waiting for processing
                node = self.nodeQueue.get(True)
                if node and len(self.nodePool)<1.5*ACTIVE_THRESHOLD:
                    self.findNode(node["host"], node["port"], newID(), node["id"])
            except Exception, err:
                print "Exception:Maintainer.start_sender()", err
        pass



    def start_service(self):
        t1 = threading.Thread(target=self.start_listener, args=())
        t1.daemon = True
        t1.start()
        t2 = threading.Thread(target=self.start_sender, args=())
        t2.daemon = True
        t2.start()
	    
        while True:
            try:
                now = time.time()
                # Should we request more nodes?
                if int(now)%5==0 and len(self.nodePool)<ACTIVE_THRESHOLD:
                    self.bootstrap()
                # Scan nodePool, kick out the dead node
                if int(now)%15==0:
                    self.scan_nodePool()
                # Cache the nodes to file
                if int(now)%10==0 and len(self.nodePool) > 1000:
                    self.serialize()
                self.info()
                
                time.sleep(1)
            except KeyboardInterrupt:
                break
            except Exception, err:
                print "Exception:Maintainer.start_service()", err
        pass

    def info(self):
        print "[NodeSet]:%i\t\t[Queue]:%i\t\t[Response]:%i" % \
              (len(self.nodePool), self.nodeQueue.qsize(), self.respondent)
        pass

    def convergeSpeed(self,node):
        if (distance(self.id, node["id"])>>148)==0:
            self.tn += 1
        if (time.time()-self.tntold) >= 5:
            self.tnspeed = int((self.tn-self.tnold)/(time.time()-self.tntold))
            self.tnold = self.tn
            self.tntold = time.time()
        pass

if __name__=="__main__":
    now = time.time()
    params = getParam(sys.argv[1:])
    print params
    
    maintainer = Maintainer(params['t'], params['id'])

    #print 'maintainer ID: ' + maintainer.id

    maintainer.start_service()
    maintainer.serialize()
    print "%.2f minutes" % ((time.time() - now)/60.0)
    pass