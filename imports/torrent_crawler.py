#!/usr/bin/python

# This script was written by David Bezdek for purpose of a master
# thesis: Torrent Peer Monitoring
# David Bezdek, xbezde11@stud.fit.vutbr.cz
# Faculty of Information Technology, Brno University of Technology
# 2018.05.23

# Checking of existing RSS file, downloading and parsing RSS file in xml format
# Result is dictionarz filesPool contains selected torrents. 

import sys
import requests
import xml.etree.ElementTree as ET
import getopt
import time
import json
import urllib3
import logging
from db_utils import *

""" examples of RSS feed URL
rssFeed = [ 
	'https://thepiratebay.org/rss/top100/201', # top 100 movies
	'https://thepiratebay.org/rss/top100/200', # top 100 videos
	'https://thepiratebay.org/rss/top100/100', # top 100 audio
	'https://thepiratebay.org/rss/top100/300'  # top 100 applications
]"""

class TorrentCrawler(object):
    def __init__(self):
        self.tree = ''
        self.filesPool = []
        #self.param = { 'r' : None, 'i' : None, 'c': None, 's': None }
        self.param = {}
        self.xmlFile = 'rss_feed.xml'
        self.newRSS = False
        
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger()
        
        self.noFilesLimit = 100
        
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        pass

    def getRSS(self, url):
        self.logger.info("Downloading RSS feed")
        self.newRSS = True
        try:
            r = requests.get(url, verify = False)
        except:
            sys.stderr.write("Error in downloading RSS feed\n")
            sys.exit(2)
    
        try:
            self.logger.info("Writing into rss_feed.xml")
            f = open(self.xmlFile, 'w')
            pom = r.text.encode('utf-8')
            f.write(pom)
            f.close()
        except:
            sys.stderr.write("Error in writing into rss file\n")
    		
        return r

    def setXMLTree(self, xmlFile):
        try:
            #self.logger.info(xmlFile)
            f = open(xmlFile, 'r')
            text = f.read()
            f.close()
        except:
            sys.stderr.write('Error in opening file: %s\n' % xmlFile)
            sys.exit(-1)
        try:
            self.tree = ET.fromstring(text)
        except:
            sys.stderr.write('Invalid xml file')
            sys.exit(-1)
        pass
    
    def getFileInfo(self, item):
        title =  item.find("title")
        infoHash = item.find('{http://xmlns.ezrss.it/0.1/}torrent/{http://xmlns.ezrss.it/0.1/}infoHash')
        #in xml file it is hex encoded infohash
        return (title.text, infoHash.text.decode("hex")) 
    
    def getFiles(self):
        try: 
            xmlFile = self.tree.find("channel")
            for item in xmlFile:
                if item.tag == "item":
                    self.filesPool.append(self.getFileInfo(item))
                    
        except:
            sys.stderr.write('Unexpected hierarchy in xml File\n')
            sys.exit(-1) 
        pass

    def check_rss(self):
        try:
            self.setXMLTree(self.xmlFile)
            self.logger.info("Reading rss_feed.xml")
        except:
            self.logger.info("Automatic downloading of RSS file")
            r = self.getRSS('https://thepiratebay.org/rss/top100/201')
            try:
                self.tree = ET.fromstring(r.content)
            except:
                sys.stderr.write('Error in creating xml file!\n')
                sys.exit(-1) 
        
        pass

    def makeJson(self):
        timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
        filename= "torrents.%s.json" % (timestamp)
        pomFiles = []
        
        #converting of infohash to printable format 
        for torr in self.filesPool:
            pomFiles.append( ( torr[0],str(intify(torr[1])) ) )
         
        try: 
            with open(filename, "w") as f:
                f.write(json.dumps(pomFiles, ensure_ascii=False))
            f.close()
        except:
            f.close()
            os.remove(filename)
            sys.stderr.write('Cant write peers into JSON, probably name of some torrent file is unsupported')
            sys.exit(-1)
      
        pass
    
    def chooseFiles(self):
        filesPoolPom = []
        if self.param['s'] != None:
            for torr in self.filesPool:
                if torr[0].find(self.param['s']) != -1:
                   filesPoolPom.append(torr)
            self.filesPool = filesPoolPom
            filesPoolPom = []
       
        #print len(self.filesPool)
                       
        if self.param['c'] != None:
            #check if param['c'] is not higher than len of filesPool
            if len(self.filesPool) > abs(self.param['c']): 
                pomRange = abs(self.param['c']) 
            else: 
                pomRange = len(self.filesPool)
            
            #adding file from the end of rss_feed
            if self.param['c'] < 0:
                maxindex = len(self.filesPool)-1
                for count in range(pomRange):
                    filesPoolPom.append(self.filesPool[maxindex-count])
            
            else:
                for count in range(pomRange):
                    filesPoolPom.append(self.filesPool[count])
            
            self.filesPool = filesPoolPom
    
    def start_crawl(self):

        if self.param['v'] != None:
            self.logger.disabled = True
        if self.param['r'] != None: #Download RSS feed
            r = self.getRSS(self.param['r'])
            try:
                self.tree = ET.fromstring(r.content)
            except:
                sys.stderr.write('Error in creating xml file!\n')
                sys.exit(-1) 
        elif self.param['i'] != None:
            self.setXMLTree(self.param['i'])
        else: #it will download static determined RSS file
            self.check_rss()
                
        self.getFiles()
        
        if self.param['c'] != None or self.param['s'] != None:
            self.chooseFiles()
        
        if self.newRSS:
            self.makeJson()
        pass
