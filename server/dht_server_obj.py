#!/usr/bin/env python3
# 
# This script was written by David Bezdek for purpose of a master
# thesis: Torrent Peer Monitoring
# David Bezdek, xbezde11@stud.fit.vutbr.cz
# Faculty of Information Technology, Brno University of Technology
# 2018.05.23

# With help of the: 
#   Martin Vasko, xvasko12@stud.fit.vutbr.cz

# Application Interface for storage of data from monitoring systems
#

import socket
import time
import re
import sys
import os
import threading
import logging

READ = '-r'
READNC = '-r-nc'
READSOC = '-r-soc'
SENDSOC = '-s-soc'
WRITE = '-s'
HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 20183              # Random number of port ( 2018 - March )
PACKET_SIZE = 2048


dtb_path = os.getcwd() + "/dtb"
sys.path.append(dtb_path) 
from set_dtb import createDtb
from fill_db_class import start_filling
from read_db_class import start_reading

class Server(object):
    
    def __init__(self, host, port):
        self.host = host
        self.port = port       
        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        
        self.noFile = 0
        self.filename = 'input'
        self.fileName = 'data'  #'dht_server_obj.py' #'dtb/fill_db_class.py' #'dht_crawler.py'  #'data'
        self.conn = None
        self.fileNames = ['ipv4nodes.json', 'ipv6nodes.json', 'torrentsAndPeers.json' , 'dht_server_obj.py' ]
        self.dtb_lock = threading.Lock()
        
        logging.basicConfig(filename='connections.log',level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger()
        pass   
        
    def sendViaSocket(self, filename):
        self.logger.info( "Sending data for socket read" )
        self.conn.settimeout(5)
        
        if not filename in self.fileNames:
            response = 'Unexpected name of file\n'
            self.logger.info( response )
            self.conn.send(response.encode())
            self.conn.shutdown(socket.SHUT_WR)
            self.conn.close()
            return
        elif os.path.exists(filename):
            self.logger.info("file exists")
        else:
            self.logger.info("file doesnt exist - need to call dtb")
            start_reading([filename])
        
        try:
            f = open(filename,'rb')
            self.logger.info( 'Sending via socket' )
            l = f.read(PACKET_SIZE)
            while (l):
                self.conn.send(l)
                l = f.read(PACKET_SIZE)
            f.close()
        except Exception as err:
            self.logger.info("Error during sending data: %s" %  err)
            pass
        self.logger.info( "Sending done\n" )
        self.conn.shutdown(socket.SHUT_WR)
        self.conn.close()
        pass
     
    def receive(self, data):
        self.logger.info( "Receiving data" )
        matchIndex = data.rfind('/')
        #print ("matchindex: %i" % matchIndex)
        if matchIndex != -1:
            filename = data[(matchIndex+1):]
        else:
            filename = data
        with open(filename, 'wb') as f:
            #f.write(data)
            self.conn.settimeout(20)
            while 1:
                try:
                    data = self.conn.recv(PACKET_SIZE)
                    if not data: 
                        self.logger.info( "No more data\n" )
                        f.close()
                        start_filling(filename)
                        response = "Data accepted\n"
                        self.conn.sendall(response.encode())                      
                        break
                    else:
                        f.write(data)
                except KeyboardInterrupt:
                    self.logger.info("keyboardInterrupt\n")
                    break
                except socket.timeout:
                    self.logger.info("Timeout - No more data\n")
                    response = "Timeout - saving data as a file\n"
                    try:
                        self.conn.sendall(response.encode())
                    except:
                        pass
                    break 
            try:
                self.conn.close()
                f.close()
            except:
                pass
        #start_reading()
        self.noFile += 1
        
        pass
                    
    def startListen(self):
        while 1:
            try:
                self.sock.listen(1)
                self.conn, addr = self.sock.accept()
                self.logger.info( "%s" % time.strftime("%Y-%m-%d--%H:%M:%S") )
                self.logger.info( 'Connected by: %s, port: %i' % ( addr[0], addr[1]) )
                data = self.conn.recv(PACKET_SIZE)
                self.logger.info(data.decode())

                if READSOC in data.decode(): #sending data
                    self.sendViaSocket(data.decode()[7:])
                #elif data.decode() == READNC: #sending data
                #    self.sendViaNetcat(addr)
                elif SENDSOC in data.decode(): #receiving data
                    self.logger.info("File:" + data.decode())
                    self.logger.info("File:" + data.decode()[7:])
                    self.receive(data.decode()[7:])
                else: 
                    response = "Unknown request\n"
                    self.conn.sendall(response.encode())
                    self.conn.close()
                    self.logger.info(response + ":" + data.decode())
            except KeyboardInterrupt:
               self.logger.info( 'keyboardInterrupt' )
               break
            except Exception as err:
               self.logger.info("Error during the action: %s" % err )
               response = str(err)
               self.conn.sendall(response.encode())
               self.conn.close()
               pass
            
        pass
    
if __name__ == '__main__':
    
    if not os.path.exists('dtb/dht_crawling.db'):
        #self.logger.info("Creating database")
        createDtb()
    server = Server(HOST, PORT)
    if '-v'in sys.argv:
        server.logger.disabled = True
    server.startListen()
    pass




