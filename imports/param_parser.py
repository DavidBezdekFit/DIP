#!/usr/bin/python

# This class was written by David Bezdek for purpose of a master
# thesis: Torrent Peer Monitoring
# David Bezdek, xbezde11@stud.fit.vutbr.cz
# Faculty of Information Technology, Brno University of Technology
# 2018.05.23

# Checking parameters from command line

import sys
import getopt

from khash import *


class ParamParser(object):
    def __init__(self):
        self.param = { 'r' : None,\
                       'i' : None,\
                       'c': None,\
                       's': None, \
                       'v': None, \
                       't': None, \
                       'id': None}
        pass

    """
    -r [--rss] URL -- URL of RSS feed
    -i [--input-announcement] filename -- already downloaded RSS feed
    -c [--set-limit] number -- choose number of files ( negative number mean files from the end )
    -s [--substr] value -- substring for choosing files - case sensitive!
    -v [--verbose] -- choose between version with or without outputs 
    -t [--type] number -- (4 or 6) choose type of crawler (IPv4 or IPv6). Implicit IPv4
    --id intified_id_format -- set id of the crawler/maintainer
    """
    def getParams(self, argv):
        
        try:
            opts, args = getopt.getopt(argv,"hv,r:i:c:s:t:",\
            ["rss=", "input-announcement=", "set-limit=", "substr=", "help", "verbose", "type=", "id="])
        except getopt.GetoptError:
            sys.stderr.write('Unexpected parameters\n') 
            self.printHelp()
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
            elif opt == '--verbose' or opt == '-v':
                self.param["v"] = True
            elif opt == '--type' or opt == '-t':
                if arg == '4' or arg == '6':
                    self.param["t"] = int(arg)
                else:
                    sys.stderr.write('Non valid value of type\n') 
                    self.printHelp()
                    sys.exit(0)
            elif opt == '--id':
                try:
                    self.param["id"] = stringify(long(arg))
                except Exception as err:
                    sys.stderr.write('Non valid value of ID\n') 
                    self.printHelp()
                    sys.exit(0)
            elif opt == '--help' or opt == '-h':
                self.printHelp()
                sys.exit(0)
            else:
                sys.stderr.write('Unknown parameter: --help\n') 
                sys.exit(1)
        pass
    
    def printHelp(self):
        helper = "Master Thesis - Monitoring BitTorrent \n"
        helper += "David Bezdek , xbezde11 , xbezde11@stud.fit.vutbr.cz , 23.05.2018\n"
        helper += "   -h [--help] - print help\n"
        helper += "   -r [--rss] URL -- URL of RSS feed\n"
        helper += "   -i [--input-announcement] filename -- already downloaded RSS feed\n"
        helper += "   -c [--set-limit] -- choose number of files ( negative number mean files from the end )\n"
        helper += "   -s [--substr] -- substring for choosing files - case sensitive!\n"
        helper += "   -v [--verbose] -- choose between version with or without outputs\n" 
        helper += "   -t [--type] number -- (4 or 6) choose type of crawler (IPv4 or IPv6). Implicit IPv4\n"
        helper += "   --id intified_id_format -- set id of the crawler/maintainer\n"
        print helper 
        pass
    
    def start_parser(self, argv):
        self.getParams(argv)        
        pass
