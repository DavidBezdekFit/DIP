#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This utilities was written by David Bezdek for purpose of a master
# thesis: Torrent Peer Monitoring
# David Bezdek, xbezde11@stud.fit.vutbr.cz
# Faculty of Information Technology, Brno University of Technology
# 2018.05.23

import os, sys
import socket

from param_parser import ParamParser

import struct
import fcntl
from khash import *

PACKET_LEN = 2048
SIZEOF_BYTE = 8

IPv6 = 6
IPv4 = 4

def unpackNodes(n):
    nodes = []
    for x in xrange(0, len(n), 26):
        id = n[x:x+20]
        ip = '.'.join([str(ord(i)) for i in n[x+20:x+24]])
        port = struct.unpack('!H', n[x+24:x+26])[0]
        nodes.append({'id':id, 'host':ip, 'port': port})
    return nodes  
        
def unpackIPv6Nodes(n):
    nodes = []
    for x in xrange(0, len(n), 38):
        id = n[x:x+20]
        ip = socket.inet_ntop( socket.AF_INET6,n[x+20:x+36])
        #print IPv6Address(Bytes(n[x+20:x+36]))
        #print ip
        port = struct.unpack('!H', n[x+36:x+38])[0]
        #print port
        nodes.append({'id':id, 'host':ip, 'port': port})
    return nodes

def unpackValues(values):
    #print "Number of peers in values: ", len(values)
    offset = 4
    peers = []
    for node in values:
        ip = socket.inet_ntop( socket.AF_INET,node[:offset])
        port = struct.unpack_from("!H", node, offset)[0]
        #if port != 1:
        peers.append((ip, port))
    return peers

def unpackValues6(values):
    #print "Number of peers in values: ", len(values)
    offset = 16
    peers = []
    for node in values:
        ip = socket.inet_ntop( socket.AF_INET6,node[:offset])
        port = struct.unpack_from("!H", node, offset)[0]
        #if port != 1:
        peers.append((ip, port))
    return peers    
    
def get_ip_address(ifname):
    
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)
    """s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])"""
    

def strxor(a, b):
        """ xor two strings of different lengths """
        if len(a) > len(b):
            return "".join([chr(ord(x) ^ ord(y)) for (x, y) in zip(a[:len(b)], b)])
        else:
            return "".join([chr(ord(x) ^ ord(y)) for (x, y) in zip(a, b[:len(a)])])
    
    
def get_port(min, max):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = min
    while True:
        try:
            s.bind(("127.0.0.1", port))
            #print 'port %i is ok' % port
            break
        except socket.error:
            #print("Port %i is already in use" %  port)
            pass
        
        if port == max:
            print 'No available port from this range'
            break
        port += 1
    s.close()
    #print "Chosen port:", port
    return port


def testBit(int_type, offset):
    mask = 1 << offset
    return(int_type & mask)

def setBit(int_type, offset):
    mask = 1 << offset
    return(int_type | mask)

def clearBit(int_type, offset):
    mask = ~(1 << offset)
    return(int_type & mask) 

def generate_zone_id(oldID, nBitZone):
    counter = 0
    byteOld = ''
    byteNew = ''
    genID = newID()
    
    for c in range(0, nBitZone):
        if (c % SIZEOF_BYTE) == 0:
            counter = 0
            index = int(c/SIZEOF_BYTE)
            #print 'c / SIZEOF_BYTE: ', index
            if index > 0:
                changingIndex = index - 1
                if changingIndex == 0:
                    genID = chr(byteNew) + genID[(changingIndex+1):]
                else:
                    genID = genID[:(changingIndex)] + chr(byteNew) + genID[(changingIndex+1):]
 
            byteOld = ord(oldID[index])
            byteNew = ord(genID[index])
            
            
        valOld = testBit(byteOld, SIZEOF_BYTE-1-counter)
        valNew = testBit(byteNew, SIZEOF_BYTE-1-counter) 
        #print c, ':', valOld, ' X ', valNew
        
        if valOld != valNew:
            if valOld == 0:
                byteNew = clearBit(byteNew, SIZEOF_BYTE-1-counter) 
            else: # == 1
                byteNew = setBit(byteNew, SIZEOF_BYTE-1-counter) #low bits first """
        counter += 1
    
    index = int((nBitZone-1)/SIZEOF_BYTE)
    #print 'index of the last changed byte: ', index
    genID = genID[:(index)] + chr(byteNew) + genID[(index+1):]
    
    return genID
    
    
def generate_injector_ids(id, nBitZone, numofIDs):
    ids = []
    id = stringify(id)
    
    for x in range(0, numofIDs):
        genID = generate_zone_id(id,nBitZone)
        ids.append(genID)
        
    return ids
    
def getParam(argv):
    parser = ParamParser()
    parser.start_parser(argv)
    return parser.param
