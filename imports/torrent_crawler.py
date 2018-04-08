#!/usr/bin/python

import sys
import requests
import xml.etree.ElementTree as ET
import getopt
import time
import json
import urllib3
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
        self.param = { 'r' : None, 'i' : None, 'c': None, 's': None }
        self.xmlFile = 'rss_feed.xml'
        self.newRSS = False
        
        self.noFilesLimit = 100
        
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        pass

    def getRSS(self, url):
        print "Downloading RSS feed"
        self.newRSS = True
        try:
            r = requests.get(url, verify = False)
        except:
            sys.stderr.write("Error in downloading RSS feed\n")
            sys.exit(2)
    
        try:
            print "Writing into rss_feed.xml"
            f = open(self.xmlFile, 'w')
            pom = r.text.encode('utf-8')
            f.write(pom)
            f.close()
        except:
            sys.stderr.write("Error in writing into rss file\n")
    		
        return r

    def setXMLTree(self, xmlFile):
        try:
            #print xmlFile
            f = open(xmlFile, 'r')
            text = f.read()
            f.close()
        except:
            sys.stderr.write('Error in opening file rss_feed.xml\n')
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
            print "Reading rss_feed.xml"
        except:
            print "Automatic downloading of RSS file"
            r = self.getRSS('https://thepiratebay.org/rss/top100/201')
            try:
                self.tree = ET.fromstring(r.content)
            except:
                sys.stderr.write('Error in creating xml file!\n')
                sys.exit(-1) 
        
        pass
    
    """
    -r [--rss] URL -- URL of RSS feed
    -i [--input-announcement] filename -- already downloaded RSS feed
    -c [--set-limit] -- choose number of files ( negative number mean files from the end )
    -s [--substr] -- substring for choosing files - case sensitive!
    """
    def _getParams(self, argv):
        
        try:
            opts, args = getopt.getopt(argv,"hr:i:c:s:",["rss=", "input-announcement=", "set-limit=", "substr=", "help"])
        except getopt.GetoptError:
            sys.stderr.write('Unexpected parameters\n') 
            self._printHelp()
            sys.exit(1)
        for opt, arg in opts:
            if opt == '-r' or opt == '--rss':
                self.param["r"] = arg
            elif opt == '-i' or opt == '--input-announcement':
                self.param["i"] = arg
            elif opt == '--set-limit' or opt == '-c':
                self.param["c"] = int(arg)
            elif opt == '--substr' or opt == '-s':
                self.param["s"] = arg
            elif opt == '--help' or opt == '-h':
                self._printHelp()
                sys.exit(0)
            else:
                sys.stderr.write('Unknown parameter: --help\n') 
                sys.exit(1)
        pass
    
    def _printHelp(self):
        helper = "Master Thesis - Monitoring BitTorrent \n"
        helper += "David Bezdek , xbezde11 , xbezde11@stud.fit.vutbr.cz , 23.05.2018\n"
        helper += "   --help - print help\n"
        helper += "   -r [--rss] URL -- URL of RSS feed\n"
        helper += "   -i [--input-announcement] filename -- already downloaded RSS feed\n"
        helper += "   -c [--set-limit] -- choose number of files ( negative number mean files from the end )\n"
        helper += "   -s [--substr] -- substring for choosing files - case sensitive!"
        print helper 
        pass
    
    def makeJson(self):
        timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
        filename= "torrents.%s.json" % (timestamp)
        pomFiles = []
        
        #converting of infohash to printable format 
        for torr in self.filesPool:
            pomFiles.append( ( torr[0],str(intify(torr[1])) ) )
        
        with open(filename, "w") as f:
            f.write(json.dumps(pomFiles, ensure_ascii=False))
        f.close()               
                    
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
    
    def start_crawl(self, argv):
        self._getParams(argv)        
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
