#!/usr/bin/env python


import socket
import Queue
import time
import threading
import json
import abc

#from struct import pack, unpack
from khash import *
from bencode import bencode, bdecode
from common import *
from db_utils import *

CTTIME = 2

class AbstractCrawler(object):
    __metaclass__ = abc.ABCMeta    
    
    @abc.abstractmethod
    def __init__(self):
        pass
    
    @abc.abstractmethod
    def start_sender(self):
        pass
    
    @abc.abstractmethod
    def serialize(self):
        """ Writing node objects into file"""
        pass    

    @abc.abstractmethod
    def info(self):
        """ Print info about nodes, queue, and so on"""        
        pass    

    @abc.abstractmethod
    def processNodes(self, nodes):
        pass    
    
    def ping(self, host, port):
        mtid = 3
        msg = bencode({"t":chr(mtid), "y":"q", "q":"ping", "a":  {"id":self.id}})
        self.isock.sendto(msg, (host,port))
        pass

    def findNode(self, host, port, target):
        mtid = 5
        msg = bencode({"t":chr(mtid), "y":"q", "q":"find_node", "a":  {"id":self.id, "target":target} })  
        #parameter "want": ["n6"] in find_node works, but IPv6 values still has to be sent over IPv6 socket
        # In other words - "n6" works for nodes, but not for "values" (reply of get_peers)
        self.isock.sendto(msg, (host,port))
        pass

    def hasNode(self, id, host, port):
        r = None
        for n in self.nodePool[id]:
            if n["host"] == host and n["port"] == port:
                r = n
                break
        return r

    def start_listener(self, searchingKey, ipv4):
        while self.counter:
            try:
                msg, addr = self.isock.recvfrom(PACKET_LEN)
                
                decMsg = bdecode(msg)
                msgContent = decMsg[decMsg['y']]
                #print msgContent
                #if searchingKey == "nodes" and "nodes" in msgContent:
                if "nodes" in msgContent:
                    self.processNodes(unpackNodes(msgContent["nodes"])) 
                if "nodes6" in msgContent:
                    self.processNodes(unpackIPv6Nodes(msgContent["nodes6"]))    
                if searchingKey == "values" and "values" in msgContent:  
                    #print "Contains values"
                    nodeID = msgContent['id']
                    torrentName = self.actualFile[0]
                    torrentID = self.actualFile[1]
                    torrentID = torrentID.encode('hex').upper()
                    if ipv4:
                        peers = unpackValues(msgContent["values"])
                    else:
                        peers = unpackValues6(msgContent["values"])
                    self.peerPool[torrentID].append( { "name" : torrentName, "nodeID" : nodeID, "peers" : peers, "nodeAddr" : addr } )
                #necessary to set because IPv6 addr = (host, port, flowinfo, scopeid)
                addrPom = ( addr[0], addr[1] )
                self.addrPool[addrPom] = {"timestamp":time.time()}
                self.respondent += 1
            except Exception, err:
                if not "v" in decMsg: 
                    #if err.code != 126: 
                    # [Errno 126] Network dropped connection on reset
                    print "Exception:Crawler.listener():", err
                    
        pass


    def start_crawl(self, ipv4):
        t1 = threading.Thread(target=self.start_listener, args=("nodes",False,))
        t1.daemon = True
        t1.start()
        t2 = threading.Thread(target=self.start_sender, args=(True,))
        t2.daemon = True
        t2.start()

        """if ipv4:
            crawler.findNode("router.bittorrent.com", 6881, self.id)
        else:
            print "crawl for ipv6"
            try:
                self.findNode("dht.transmissionbt.com", 6881, self.id) # reply on want n6 -- combination n4 and n6 no reply,                                                        #sometimes it doesnt reply even on n6 
                self.findNode("router.silotis.us", 6881, self.id)
            except Exception, err:
                print "IPv6 central router is not available", err
            time.sleep(3)"""
        print "\nStart bootstrapping"        
        while self.counter:
            try:
                self.counter = CTTIME if self.nodeQueue.qsize() else self.counter-1
                self.info()
                time.sleep(1)
            except KeyboardInterrupt:
                print "\nKeyboard Interrupt - start_crawl()"
                self.counter = 0
                break
            except Exception, err:
                print "Exception:Crawler.start_crawl()", err
        pass
