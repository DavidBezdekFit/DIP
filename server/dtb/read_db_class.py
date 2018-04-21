#!/usr/bin/env python3
# 
# script for read the database for dht crawling
# author: David Bezdek, xbezde11@stud.fit.vutbr.cz
# Faculty of Information Technology, Brno University of Technology
# 23. 5. 2018



import socket
import time
import sys
import os
import fnmatch
import json
import sqlite3

IPv4 = 4
IPv6 = 6   

class Database(object):
    
    def __init__(self):
        self.dtbName = 'dtb/dht_crawling.db'
        self.conn = sqlite3.connect(self.dtbName)
        pass
        
    def getNodes(self, type):
        c = self.conn.cursor()
        c.execute('SELECT * FROM Node WHERE type=?', str(type))
        count = 0
        nodes = {}
        for row in c:
            nodes[row[0]] = { "host" : row[2], "port": row[3], "timestamp" : row[4] }
            count += 1
        print ("length of Node type: ipv%i is:" % type, count)
        filename = "ipv" + str(type) + "nodes.json"
        print ('Creating ',filename)
        
        with open(filename, "w") as f:
            f.write(json.dumps(nodes, ensure_ascii=False))
        f.close() 
        pass
        
    def getPeersOfFile(self, infohash):
        e = self.conn.cursor()
        peers = []
        e.execute('SELECT host, port, timestamp FROM File_Peer JOIN Peer ON peer_id=host WHERE file_id=?', (infohash,) )
        for peer in e:
            #print (peer)
            pomPeer = { "addr": [peer[0], peer[1]]  , "timestamp" : peer[2] }
            peers.append( pomPeer )
        return peers
        
    def makePeers(self):
        d = self.conn.cursor()
        d.execute('SELECT * FROM File JOIN File_Node ON infohash=file_id JOIN Node ON node_id=nodeID')
        pool = {}

        for file_node in d:
        
            infohash = file_node[0]
            #if not exists key infohash
            if not infohash in pool:
                pool[infohash] = { "peers": [], "nodes" : [], "name" : file_node[1]}

            nodeID = file_node[3]
            host = file_node[6]
            port = file_node[7]
            timestamp = file_node[8]
            
            node = { "timestamp": timestamp, "nodeID": nodeID, "nodeAddr": [host, port] }
            pool[infohash]["nodes"].append( node )
            
            #there should be no duplicates file-peer (unique in table set), so extend can be used
            pool[infohash]["peers"].extend( self.getPeersOfFile(infohash) )

        filename= 'torrentsAndPeers.json'
        print ('Creating ', filename)
        with open(filename, "w") as f:
            f.write(json.dumps(pool, ensure_ascii=False))
        f.close()          
        pass
    
def start_reading(filename):

    dtb = Database()
    c = dtb.conn.cursor()

    if 'ipv4nodes.json' in filename:
        dtb.getNodes(IPv4)
    if 'ipv6nodes.json' in filename:
        dtb.getNodes(IPv6)
    if 'torrentsAndPeers.json' in filename:
        dtb.makePeers()

    dtb.conn.close()
    pass

