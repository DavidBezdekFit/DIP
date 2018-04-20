#!/usr/bin/env python3
# 
# 
#
#

import socket
import time
import sys
import os
import threading

READ = '-r'
READNC = '-r-nc'
READSOC = '-r-soc'
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
        self.fileNames = ['ipv4nodes.json', 'ipv6nodes.json', 'torrentsAndPeers.json' ]
        self.dtb_lock = threading.Lock()
        pass   
        
    def sendViaSocket(self):
        print ( "Sending data for socket read" )
        self.conn.settimeout(2)
        #call class for create actual file from database!! and set fileName
        #start_reading()
        try:
            f = open(self.fileName,'rb')
            print ( 'Sending via socket' )
            l = f.read(PACKET_SIZE)
            while (l):
                self.conn.send(l)
                l = f.read(PACKET_SIZE)
            f.close()
        except Exception as err:
            print ("Error during sending data:",  err)
            pass
        print ( "Sending done\n" )
        self.conn.shutdown(socket.SHUT_WR)
        self.conn.close()
        pass

    def sendViaSocket2(self, filename):
        print ( "Sending data for socket read" )
        self.conn.settimeout(2)
        #call class for create actual files from database
        
        
        if os.path.exists(filename):
            print ("file exists")
        else:
            print ("file doesnt exist - need to call dtb")
            start_reading([filename])
        
        try:
            f = open(filename,'rb')
            print ( 'Sending via socket' )
            l = f.read(PACKET_SIZE)
            while (l):
                self.conn.send(l)
                l = f.read(PACKET_SIZE)
            f.close()
        except Exception as err:
            print ("Error during sending data:",  err)
            pass
        print ( "Sending done\n" )
        self.conn.shutdown(socket.SHUT_WR)
        self.conn.close()
        pass
      
    def sendViaNetcat(self, addr):
        print ( "Sending data for nc -6" )
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        #sock.bind(("",PORT+1))
        sock.settimeout(2)
        time.sleep(0.5)
        try:
            sock.connect((addr[0], PORT+1))
        except socket.timeout:
            print ("Timeout")
            raise
        except Exception as err:
            print (err)
            raise
        #call class for create actual file from database!! and set fileName
        try:
            f = open(self.fileName,'rb')
            print ( 'Sending via socket' )
            l = f.read(PACKET_SIZE)
            while (l):
                sock.send(l)
                l = f.read(PACKET_SIZE)
            f.close()
        except Exception as err:
            print ("Error in reading or sending data file:", err)
            pass
        print ( "Sending done\n" )
        sock.shutdown(socket.SHUT_WR)
        sock.close()
        pass
     
    def receive(self, data):
        print ( "Receiving data" )
        filename = data
        with open(filename, 'wb') as f:
            #f.write(data)
            self.conn.settimeout(2)
            while 1:
                try:
                    data = self.conn.recv(PACKET_SIZE)
                    if not data: 
                        print ( "No more data\n" )
                        f.close()
                        start_filling(filename)
                        response = "Data accepted\n"
                        self.conn.sendall(response.encode())                      
                        break
                    else:
                        f.write(data)
                except KeyboardInterrupt:
                    print ("keyboardInterrupt\n")
                    break
                except socket.timeout:
                    print ("Timeout - No more data\n")
                    response = "Timeout - saving data as a file\n"
                    self.conn.sendall(response.encode())
                    break
            self.conn.close()
             
            try:
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
                print ( 'Connected by', addr )
                data = self.conn.recv(PACKET_SIZE)
                print (data.decode())
                if data.decode() == READSOC: #sending data
                    self.sendViaSocket()
                elif READSOC in data.decode():
                    self.sendViaSocket2(data.decode()[7:])
                elif data.decode() == READNC: #sending data
                    self.sendViaNetcat(addr)
                else: #receiving data
                    print ("File:", data.decode())
                    self.receive(data.decode())
                    
            except KeyboardInterrupt:
               print ( 'keyboardInterrupt' )
               break
            except Exception as err:
               print ("Error during the action:", err, "\n")
               pass
            
        pass
    
if __name__ == '__main__':
    
    if not os.path.exists('dtb/dht_crawling.db'):
        print ("Creating database")
        createDtb()
    server = Server(HOST, PORT)
    server.startListen()
    pass



