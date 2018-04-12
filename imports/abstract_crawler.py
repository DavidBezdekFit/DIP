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
    def info(self):
        """ Print info about nodes, queue, and so on"""        
        pass    

    @abc.abstractmethod
    def processNodes(self, nodes):
        pass    
        
    def my_bind(self, str, port):
        while True:
            try:
                self.isock.bind( (str,self.port) )
                break
            except socket.error:
                self.port += 1
                pass
            
        self.logger.info("Chosen port: %i" % self.port)
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

    def find_routers(self):
        if self.type == IPv4:
            try:
                self.findNode("router.bittorrent.com", 6881, self.id)
            except:
                print "Can not connect to central router router.bittorrent.com"
                sys.exit(0)
        else:
            try:
                self.findNode("dht.transmissionbt.com", 6881, self.id) # reply on want n6 -- combination n4 and n6 no reply, 
            except:
                print "Can not connect to central dht.transmissionbt.com"
                pass
            try:
                self.findNode("router.silotis.us", 6881, self.id) 
            except:
                print "Can not connect to central router router.silotis.us"
                pass
        pass
        
    def hasNode(self, id, host, port):
        r = None
        for n in self.nodePool[id]:
            if n["host"] == host and n["port"] == port:
                r = n
                break
        return r
        
    def saveNodes(self,timestamp):
        obj = {}
        for k, nlist in self.nodePool.items():
            for v in nlist:
                addr = (v['host'], v['port'])
                if addr in self.addrPool:
                    v["rtt"] = self.addrPool[addr]["timestamp"]- v["timestamp"]
                obj[k] = obj.get(k, []) + [v]
        

        #store nodePool
        obj3 = {}
        for infohash in obj:
            for dict in obj[infohash]:
                lv_timestamp = dict["timestamp"]
                pomid = str(intify(infohash))
                host = dict['host']
                port = dict['port']
                obj3[pomid] = { "host" : host, "port" : port, "timestamp" : lv_timestamp } 
        self.logger.info( "Saving Nodes" )    
        filename= "ipv%snodes.%s.%s.json" % (str(self.type),timestamp, str(intify(self.id)))
        with open(filename, "w") as f:
            f.write(json.dumps(obj3, ensure_ascii=False))
        f.close()        


    def start_listener(self, searchingKey):
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
                    if self.type == IPv4:
                        peers = unpackValues(msgContent["values"])
                    elif self.type == IPv6:
                        peers = unpackValues6(msgContent["values"])
                    else:
                        self.logger.info("Non valid type of IP protocol!")
                    self.peerPool[torrentID].append( { "name" : torrentName, "nodeID" : nodeID, "peers" : peers, "nodeAddr" : addr } )
                #necessary to set because IPv6 addr = (host, port, flowinfo, scopeid)
                addrPom = ( addr[0], addr[1] )
                self.addrPool[addrPom] = {"timestamp":time.time()}
                self.respondent += 1
            except Exception, err:
                if not "v" in decMsg: 
                    #if err.code != 126: 
                    # [Errno 126] Network dropped connection on reset
                    self.logger.info("Exception:Crawler.listener(): %s" % err)
                    
        pass


    def start_crawl(self):
        t1 = threading.Thread(target=self.start_listener, args=("nodes",))
        t1.daemon = True
        t1.start()
        t2 = threading.Thread(target=self.start_sender, args=(True,))
        t2.daemon = True
        t2.start()

        # collect some nodes for start
        self.find_routers()
        self.logger.info( "\nStart bootstrapping" )       
        while self.counter:
            try:
                self.counter = CTTIME if self.nodeQueue.qsize() else self.counter-1
                self.info()
                time.sleep(1)
            except KeyboardInterrupt:
                self.logger.info( "\nKeyboard Interrupt - start_crawl()" )
                self.counter = 0
                break
            except Exception, err:
                self.logger.info("Exception:Crawler.start_crawl(): %s" % err)
        pass
        
    
