#!/usr/bin/env python
# 
# script for set the database for dht crawling
# author: David Bezdek, xbezde11@stud.fit.vutbr.cz
# 23. 5. 2018


import socket
import time
import sys

import sqlite3



class Database(object):
    
    def __init__(self):
        self.dtbName = 'dtb/dht_crawling.db'
        self.conn = sqlite3.connect(self.dtbName)
        pass

def createDtb():

    dtb = Database()
    
    c = dtb.conn.cursor()

    try:
        c.execute("DROP TABLE File_Peer")
        c.execute("DROP TABLE File_Node")
        c.execute("DROP TABLE Peer_Node")
        c.execute("DROP TABLE File")
        c.execute("DROP TABLE Peer")
        c.execute("DROP TABLE Node")
    except:
        pass
    # Create table
    c.execute('''CREATE TABLE IF NOT EXISTS Node (
                nodeID text primary key,
                type integer,
                host text,
                port integer,
                timestamp text) ''')  #type ipv4/ ipv6
                # foreign key peers  -- 0..*
                # foreign key files - 0..*
    c.execute('''CREATE TABLE IF NOT EXISTS Peer (
                host text primary key,
                type integer,
                port integer,
                timestamp text) ''')
                # !!! foreign key nodes  -- 1..*
                # foreign key files - 1..*
    c.execute('''CREATE TABLE IF NOT EXISTS File (
                infohash text primary key,
                name text) ''')
                # !!! foreign key peers  -- 0..*
                # foreign key nodes - 1..*              

    # many to many relationships
    c.execute('''CREATE TABLE IF NOT EXISTS File_Peer (
                file_id text,
                peer_id text,
                FOREIGN KEY(file_id) REFERENCES File(infohash),
                FOREIGN KEY(peer_id) REFERENCES Peer(host),
                unique (file_id, peer_id)) ''')
                
    c.execute('''CREATE TABLE IF NOT EXISTS File_Node (
                file_id text,
                node_id text,
                FOREIGN KEY(file_id) REFERENCES File(infohash),
                FOREIGN KEY(node_id) REFERENCES Node(nodeID),
                unique (file_id, node_id)) ''')
                
    c.execute('''CREATE TABLE IF NOT EXISTS Peer_Node (
                peer_id text,
                node_id text,
                FOREIGN KEY(peer_id) REFERENCES Peer(host),
                FOREIGN KEY(node_id) REFERENCES Node(nodeID),
                unique (peer_id, node_id)) ''')
    
    
    # Save (commit) the changes
    dtb.conn.commit()
    dtb.conn.close()
    print ("Database established successfuly")

