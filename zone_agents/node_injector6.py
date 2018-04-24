#!/usr/bin/env python
# 
# This script is an experimental injector into MLDHT.
#
# Liang Wang @ Dept. Computer Science, University of Helsinki
# 2011.09.21
#

# 
# Modified by: David Bezdek, xbezde11@stud.fit.vutbr.cz
# Faculty of Information Technology, Brno University of Technology
# 23. 5. 2018


import os
import sys
import socket
import pickle
import time
import threading
import resource
import fnmatch

imports_path = os.getcwd() + "/../imports/"
sys.path.append(imports_path) 

from khash import *
from bencode import bencode, bdecode
from common import *
from multiprocessing import *
from db_utils import *

BUCKET_LIMIT = 8

TID = 't'
REQ = 'q'
RSP = 'r'
TYP = 'y'
ARG = 'a'
ERR = 'e'

class Injector(object):
    def __init__(self, counter, id = None):
        self.noisy = True                                       # Output extra info or not
        self.id = id if id else newID()                         # Injector's ID
        self.injID = counter
        self.ip = "2001:67c:1220:c1b1:4582:871a:2b8c:8088"      # my ip
        self.port = get_port(30000,31000)                       # my listening port
        self.buckets = []                                       # Bucket structure holding the known nodes
        self.nodePool = {}                                      # Dict of the nodes collected
        self.addrPool = {}                                      # Dict uses <ip,port> as its key
        self.nodeQueue = Queue(0)                               # Queue of the nodes to scan
        self.counter = 5                                        # How long to wait after a queue is empty
        self.startTime = time.time()                            # Time start the injector
        self.duplicates = 0                                     # How many duplicates among returned nodes
        self.total = 1                                          # Total number of returned nodes
        self.respondent = 0                                     # Number of respondent
        self.tn = 0                                             # Number of nodes in a specified n-bit zone
        self.tnold = 0
        self.tntold = 0
        self.tnspeed = 0
        self.ndist = 2**160-1

        self.isock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        #self.isock.bind( ("",self.port) )
        self.my_bind("",self.port)
        self.isock_lock = threading.Lock()
        pass
    
    def my_bind(self, str, port):
        while True:
            try:
                self.isock.bind( (str,self.port) )
                print 'port %i is ok' % self.port
                break
            except socket.error as e:
                #print("Port %i is already in use" %  port)
                pass
        
            self.port += 1
        

    def add_to_bucket(self, node):
        """Add a node into the bucket, the interval is like this [x,y)"""
        if not len(self.buckets):
            self.buckets = [ [[0,2**160], []] ]
        id = intify(node["id"])
        bucket = None
        # Find the proper bucket for the now node
        for x in self.buckets:
            r, nl = x
            if id >= r[0] and id < r[1]:
                bucket = x
                break
        # OK, find the bucket for the new node
        if bucket:
            r, nl = bucket
            # If the bucket id full
            if len(nl) >= BUCKET_LIMIT:
                # if the new node 'near to me'?
                if self.is_in_bucket(self.id, bucket):
                    # split the bucket
                    x, y = r
                    m = ((y-x)>>1) + x
                    new_bucket = [ [x,m], [] ]
                    bucket[0] = [m,y]
                    pos = self.buckets.index(bucket)
                    self.buckets.insert(pos, new_bucket)
                    for n in nl:
                        tid = intify(n["id"])
                        if tid < m:
                            nl.remove(n)
                            new_bucket[1].append(n)
                    # Recursion
                    self.add_to_bucket(node)
                    pass
                # if the node is far from me and the bucket if full, drop it.
                else:
                    pass
            # OK, we have spare place for new nodes.
            else:
                nl.append(node)
        pass

    def remove_from_bucket(self, id, buckets):
        """Remove a node from a bucket"""
        bucket = self.in_which_bucket(id, buckets)
        node = self.is_in_bucket(id, bucket)
        bucket[1].remove(node)
        # if the bucket is empty, then merge with others
        if len(bucket[1])==0 and len(buckets)>1:
            x, y = bucket[0]
            pos = buckets.index(bucket)
            prev = max(pos-1,0)
            next = min(pos+1,len(buckets)-1)
            px, py = buckets[prev][0]
            nx, ny = buckets[next][0]
            if pos==prev or ( pos!=prev and (ny-nx)==(y-x) ):
                buckets[next][0] = [x,ny]
            elif pos==next or ( pos!=next and (py-px)==(y-x) ):
                buckets[prev][0] = [px,y]
            buckets.remove(bucket)
        pass

    def is_in_bucket(self, id, bucket):
        """Given the id and the bucket, check if the id is in the bucket"""
        node = None
        r, nl = bucket
        for n in nl:
            if id == n['id']:
                node = n
                break
        return node

    def in_which_bucket(self, id, buckets):
        """Given the id, check which bucket it is in"""
        b = None
        for bucket in buckets:
            if self.is_in_bucket(id, bucket):
                b = bucket
                break
        return b

    def bootstrap(self):
        """Bootstrap myself"""
        self.add_to_bucket({"id":self.id, "host":self.ip, "port":self.port})
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

    def nearest(self, target, nl, limit=None):
        """Given the node list and the target id, return the nearest ones."""
        l= []
        for n in nl:
            l += [(distance(n["id"], target), n)]
        l.sort()
        m = [ n[1] for n in l[:limit] ]
        return m

    def ping(self, host, port):
        #msg = self.krpc.encodeReq("ping", {"id":self.id})
        mtid = 3
        msg = bencode({"t":chr(mtid), "y":"q", "q":"ping", "a":  {"id":self.id}})
        self.sendMsg(msg, (host, port))
        pass

    def findNode(self, host, port, target):
        #msg = self.krpc.encodeReq("find_node", {"id":self.id, "target":target})
        mtid = 5
        msg = bencode({"t":chr(mtid), "y":"q", "q":"find_node", "a":  {"id":self.id, "target":target}})
        
        self.sendMsg(msg, (host,port))
        pass

    def processNodes(self, nodes):
        timestamp = time.time()
        nodes = self.nearest(self.id, nodes, 10) #3
        for node in nodes:
            id = node["id"]
            node["timestamp"] = timestamp
            node["rtt"] = float('inf')
            if id not in self.nodePool:
                self.nodePool[id] = [node]
                self.convergeSpeed(node)
                if id != self.id:
                    self.findNode(node["host"], node["port"], self.id)
            else:
                if not self.hasNode(node["id"], node["host"], node["port"])\
                       and id != self.id:
                    self.nodePool[id].append(node)
                else:
                    self.duplicates += 1
            self.total += 1
        pass

    def hasNode(self, id, host, port):
        r = None
        for n in self.nodePool[id]:
            if n["host"] == host and n["port"] == port:
                r = n
                break
        return r

    def sendMsg(self, msg, addr):
        """Send the message through isock, thread safe"""
        self.isock_lock.acquire()
        try:
            self.isock.sendto(msg, addr)
        except Exception, err:
            print "Exception:Injector.sendMsg():", err
        self.isock_lock.release()
        pass

    def serialize(self):
        obj = {}
        for k, nlist in self.nodePool.items():
            for v in nlist:
                addr = (v['host'], v['port'])
                if addr in self.addrPool:
                    v["rtt"] = self.addrPool[addr]["timestamp"]- v["timestamp"]
                obj[k] = obj.get(k, []) + [v]

        timestamp = time.strftime("%Y%m%d%H%M%S")
        f = open("nodes6.%s.%s" % (timestamp, str(intify(self.id))), "w")
        pickle.Pickler(f).dump(obj)
        f.close()
        pass

    def start_listener(self):
        """Process all the incomming messages here"""
        while self.counter:
            try:
                msg, addr = self.isock.recvfrom(PACKET_LEN)
                d = bdecode(msg)

                ts = time.time()

                # Add to bucket if it is a new node, otherwise update it.
                MSG = d[TYP]
                tid = d[RSP]["id"] if d[TYP] == RSP else d[ARG]["id"]
                bucket = self.in_which_bucket(tid, self.buckets)
                if bucket:
                    pass
                else:
                    n = {"id":tid, "timestamp":ts, "lastupdate":ts}
                    self.add_to_bucket(n)
                # Process message according to their message type
                if d[TYP] == RSP:
                    if "nodes6" in d[MSG]:
                        tdist = distance(self.id, d[MSG]["id"])
                        if tdist < self.ndist:
                            self.ndist = tdist
                            self.processNodes(unpackIPv6Nodes(d[MSG]["nodes6"]))
                            #print tdist, "+"*100
                        elif self.respondent < 10000:
                            self.processNodes(unpackIPv6Nodes(d[MSG]["nodes6"]))
                elif d[TYP] == REQ:
                    #print addr, d[TID], d[TYP], d[MSG], d[ARG]
                    if "ping" == d[MSG].lower():
                        rsp = {TID:d[TID], TYP:RSP, RSP:{"id":self.id}}
                        #rsp = self.krpc.encodeMsg(rsp)
                        rsp = bencode(rsp)
                        self.sendMsg(rsp, addr)
                        pass
                else:
                    pass
                #self.addrPool[addr] = {"timestamp":time.time()}
                self.respondent += 1
            except Exception, err:
                print "Exception:Injector.listener():", err
        pass

    def start_sender(self): # findNode(self, host, port, target):
        target = self.id
        while self.counter:
            try:
                node = self.nodeQueue.get(True)
                #self.findNode(node["host"], node["port"], target)
                self.findNode(node["host"], node["port"], node["id"])
            except Exception, err:
                print "Exception:Injector.start_sender()", err, node
        pass

    def start(self):
        t1 = threading.Thread(target=self.start_listener, args=())
        t1.daemon = True
        t1.start()
        #for IPv4 was t2 as comment !!!
        t2 = threading.Thread(target=self.start_sender, args=())
        t2.daemon = True
        t2.start()
        self.bootstrap()
        while True:
            try:
                self.info()
                time.sleep(5)
            except KeyboardInterrupt:
                break
            except Exception, err:
                print "Exception:Injector.start_crawl()", err
        pass

    def info(self):
        print "%i:[NodeSet]:%i\t\t[12-bit Zone]:%i [%i/s]\t\t[Response]:%.2f%%\t\t[Queue]:%i\t\t[Dup]:%.2f%%" % \
              (self.injID,len(self.nodePool), self.tn, self.tnspeed,
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

    def test_bucket(self):
        self.bootstrap()
        id_set = set()
        #print "Add"
        for i in range(50000):
            id = newID()
            node = {"id":id}
            self.add_to_bucket(node)
            id_set.add(id)
        for x in self.buckets:
            print len(x[1])

        #print "Remove"
        for id in id_set:
            if self.in_which_bucket(id, self.buckets):
                self.remove_from_bucket(id, self.buckets)
                pass
        for x in self.buckets:
            print len(x[1])

        pass
        
    #read some additional address for better bootstraping
    def loadCache(self):
        print("Loading Cache")
        try:
            pomFile = "nodes6cache*"
            for fileName in os.listdir('.'):
                if fnmatch.fnmatch(fileName, pomFile):
                    #print("Loading File: %s" % fileName)
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

def start_injecting(id, counter):
    """Start all the injectors"""
    injector = Injector(counter, id)
    injector.loadCache()
    
    injector.start()
    pass
    
def getIDs(id):
    ids = []
    # Check if the injector_ids.txt exists or not
    if os.path.exists("injector_ids_%s.txt" % intify(id)):  #every call is with newID
        f = open("injector_ids_%s.txt" % intify(id), "r")
        for line in f.readlines():
            ids.append(stringify(long(line)))
    """else:
        print "vytvarim nove"
        ids = generate_injector_ids(intify(id), 12, 50)
        f = open("injector_ids_%s.txt" % str(intify(id)), "w")
        for tid in ids:
            i = intify(tid)
            f.write("%s\n" % str(i))
        f.close()"""
    return ids

if __name__=="__main__":    
    now = time.time()
    
    id = stringify(long(sys.argv[1])) if len(sys.argv)>1 else newID()
    
    ids = getIDs(id)
    
    counter = 0
    for tid in ids:
        #print intify(tid)
        try:
            p = Process(target=start_injecting, args=(tid,counter,))
            p.start()
        except KeyboardInterrupt:
            break
        except:
            pass
        counter += 1

    # injector = Injector(id)
    #  Try to load local node cache
    # try:
    #     if os.path.exists("nodecache"):
    #         nl = pickle.load(open("nodecache","r"))
    #         for n in nl:
    #             n["timestamp"] = time.time()
    #             n["rtt"] = float('inf')
    #             injector.nodeQueue.put(n)
    # except:
    #     pass
    # injector.test_bucket()
    #  Try to get bootstrap nodes from official router
    # injector.findNode("router.bittorrent.com", 6881, injector.id)
    # injector.bootstrap()
    # injector.start()

    #print "%.2f minutes" % ((time.time() - now)/60.0)
    #injector.serialize()
    pass
