#!/usr/bin/env python3
# 
# script for fill the database for dht crawling
# author: David Bezdek, xbezde11@stud.fit.vutbr.cz
# 23. 5. 2018


import socket
import time
import sys
import os
import fnmatch
import json
import sqlite3

def intify(hstr):
    """20 bit hash, big-endian -> long python integer"""
    assert len(hstr) == 20
    return long(hstr.encode('hex'), 16)
  
def stringify(num):
    """long int -> 20-character string"""
    str = hex(num)[2:]
    if str[-1] == 'L':
        str = str[:-1]
    if len(str) % 2 != 0:
        str = '0' + str
    #str = str.decode('hex')
    return (20 - len(str)) *'\x00' + str

class Database(object):
    
    def __init__(self):
        self.dtbName = 'dtb/dht_crawling.db'
        self.conn = sqlite3.connect(self.dtbName)
        pass
        

    def getType(self, host):
        if host.find(':') == -1:
            type = 4
        else: 
            type = 6
        return type
        
    def getJsonData(self, filename):
        try:
            f = open(filename, 'r')
            text = f.read()
            dataJson = json.loads(text)
        except:
            print ("Error in reading file")
            raise
        return dataJson
        
    def insertNodes(self, info):
        duplicates = 0
        c = self.conn.cursor()
        try:
            c.execute("INSERT INTO Node (nodeID, type, host, port, timestamp) VALUES (?,?,?,?,?)", (info[0], info[1], info[2], info[3], info[4] ) )
        except sqlite3.IntegrityError as err:
            #print ("Dupliace klicu")
            duplicates += 1
            c.execute("UPDATE Node SET type = ?, host = ?, port = ?, timestamp=? WHERE nodeID=?", ( info[1], info[2], info[3], info[4] ,info[0] ) ) 
        except Exception as err:
            print (err)
            pass
        return duplicates
        
    def saveNodes(self, filename):
        print ("Saving nodes")
        print ("File:",filename)
        try:
            dataJson = self.getJsonData(filename)
        except Exception as err:
            print (err)
            return

        print ("Saving into database")
        starttime = time.time()
        duplicates = 0
       
        for infohash in dataJson:
            type = self.getType(dataJson[infohash]["host"])
            duplicates += self.insertNodes( (infohash, type, dataJson[infohash]["host"], dataJson[infohash]["port"], dataJson[infohash]["timestamp"]) )

        endtime = time.time()
        duration = ((endtime-starttime) % 60)
        print ("Duration time: %i sec" % int(duration) )
        print ("Number of nodes:", len(dataJson))
        print ("Number of dupl :", duplicates)
        pass
       
    def saveFiles(self, filename):
        print ("Saving torrents")
        print ("File:",filename)
        try:
            dataJson = self.getJsonData(filename)
        except Exception as err:
            print (err)
            return
        c = self.conn.cursor()    
        for key in dataJson:
            # converting to format corresponding to the rss_feed
            #print ( (stringify(int(key[1]))).upper() )
            try:
                c.execute("INSERT INTO File (infohash, name) VALUES (?,?)", ( stringify(int(key[1])).upper() , key[0] ) )
            except sqlite3.IntegrityError as err:
                #print ("Key duplication - nothing to update in files")
                pass
            except Exception as err:
                print (err)
                pass
        pass
    
        
    def savePeers(self, filename):
        print ("Saving peers")
        print ("File:",filename)
        try:
            dataJson = self.getJsonData(filename)
        except Exception as err:
            print (err)
            return
        c = self.conn.cursor()
        duplicates = 0
        peerCount = 0
        for infohash in dataJson:
            #print ( infohash )
            #print ( dataJson[infohash] )
            
            try: #saving file
                c.execute("INSERT INTO File (infohash, name) VALUES (?,?)", (infohash, "") )
            except sqlite3.IntegrityError as err:
                #if it already exists, no need to update
                pass
            except Exception as err:
                print (err)
                pass    
            
            #print ("Saving nodes from peers")
            for node in dataJson[infohash]["nodes"]:    
                type = self.getType(node["nodeAddr"][0])
                #saving nodes
                self.insertNodes( (node["nodeID"], type, node["nodeAddr"][0], node["nodeAddr"][1], node["timestamp"]) )
                    
                try: #saving to the table for many to many relationships: File_Peer
                    c.execute("INSERT INTO File_Node  (file_id, node_id) VALUES (?,?)", ( infohash, node["nodeID"] ) )
                except sqlite3.IntegrityError as err:
                    pass
                except Exception as err:
                    print (err)
                    pass    
            
            #print ("Saving Peers")
            for peer in dataJson[infohash]["peers"]:
                #print (peer)
                type = self.getType(peer["addr"][0])
                try: #saving peers
                    peerCount += 1
                    c.execute("INSERT INTO Peer (host, type, port, timestamp) VALUES (?,?,?,?)", (peer["addr"][0], type, peer["addr"][1], peer["timestamp"]) )
                except sqlite3.IntegrityError as err:
                    c.execute("UPDATE Peer SET port = ?, timestamp=? WHERE host=?", (peer["addr"][1], peer["timestamp"], peer["addr"][0]) )
                    # host should not change same as type
                    duplicates += 1
                    pass
                except Exception as err:
                    print (err)
                    pass
                #print ("Saving File_Peer")    
                try: #saving to the table for many to many relationships: File_Peer
                    c.execute("INSERT INTO File_Peer  (file_id, peer_id) VALUES (?,?)", ( infohash, peer["addr"][0] ) )
                except sqlite3.IntegrityError as err:
                    pass
                except Exception as err:
                    print (err)
                    pass 
                #print ("Saving Peer_Node")  
                for node in dataJson[infohash]["nodes"]:     
                    try: #Peer_Node
                        c.execute("INSERT INTO Peer_Node  (peer_id, node_id) VALUES (?,?)", ( peer["addr"][0],  node["nodeID"] ) )
                    except sqlite3.IntegrityError as err:
                        pass
                    except Exception as err:
                        print (err)
                        pass 

        print ("Number of peers:", peerCount)
        print ("Number of dupl :", duplicates)        
        pass
   
    
def start_filling(filename):

        dtb = Database()
        
        c = dtb.conn.cursor()

        print ("Loading File for database:", filename)
        if filename[len(filename)-3:] != ".py" and filename[len(filename)-3:] != ".db":
            if filename.find("node") != -1:
                dtb.saveNodes(filename)
            elif filename.find("torrent") != -1:    
                dtb.saveFiles(filename)
            elif filename.find("peer") != -1:
                dtb.savePeers(filename)
                
            try:
                os.remove(filename)
            except OSError:
                pass   
            print ("\n")       

        dtb.conn.commit()
        
        dtb.conn.close()

