#!/usr/bin/python
# 
# This script is used parse the log file generated by the crawler.
# Currently, it will map the ip address to its geo-location. The
# file and its structure might be reorganized in futuren when more
# features are needed.
#
# By Liang Wang @ Dept. Computer Science, University of Helsinki
# 2010.12.01
#

# This script was modified by David Bezdek for purpose of a master
# thesis 
# David Bezdek, xbezde11@stud.fit.vutbr.cz
# Faculty of Information Technology, Brno University of Technology
# 2018.05.23


# This script use IP2Location LITE database under this licence:
# All sites, advertising materials and documentation mentioning features
# or use of this database must display the following acknowledgment:
# This site or product includes IP2Location LITE data available from
# http://www.ip2location.com.
# IP2Location is a registered trademark of Hexasoft Development Sdn Bhd. 
# All other trademarks are the property of their respective owners.



import os, sys
import pickle
import sqlite3 as sqlite
import signal
from binascii import hexlify
import socket
import json

from datetime import datetime

IP_DB_FILE = "./ip.db"
IP_DB_FILE6 = "./ip6.db"
IPv4 = 4
IPv6 = 6

class IPDB(object):
    def __init__(self, db=IP_DB_FILE):
        self.conn = sqlite.connect(db)
        self.cur = self.conn.cursor()
        
        self.conn6 = sqlite.connect(IP_DB_FILE6)
        self.cur6 = self.conn6.cursor()
        pass

    def ip2loc(self, ip):
        i = self.ip2int(ip)
        self.cur.execute("select * from iplocs where ip_start<=? order by ip_start desc limit 1;", (i,))
        for r in self.cur:
            """return {"ip":ip, "country_code":r[1], "country_name":r[2],\
                    "region_code":r[3], "region_name":r[4], "city":r[5],\
                    "zipcode":r[6], "latitude":r[7], "longtitude":r[8],\
                    "metrocodde":r[9]}"""
            return {"ip":ip, "country_code":r[2], "country_name":r[3],\
                    "city":r[4]}

    def ip2int(self, ip):
        a = ip.split(".")
        k = 0
        for i in range(4):
            k = (k<<8) + int(a[i])
        return k
        
    def ipv6_2loc(self, ip):
        i = str(self.ipv6_2int(ip))
        self.cur6.execute("select * from iplocs where ip_start<=? order by ip_start desc limit 1;", (i,))
        for r in self.cur6:
            return {"ip":ip, "country_code":r[2], "country_name":r[3],\
                    "city":r[4]}

    def ipv6_2int(self, ip):
        return int(hexlify(socket.inet_pton(socket.AF_INET6, ip)), 16)


    def debug(self):
        # Put test code here.
        pass


class Parser(object):
    def __init__(self, dup = "-id"):
        self.ipdb = IPDB()
        #self.set_enum(dup)
        pass


    def get_type(self, host):
        if host.find(':') == -1:
            htype = IPv4
        else:
            htype = IPv6
        return htype

    def geoDistribution(self, dataJson, col = "country_name"):
        geo = {"unknown":0}
        city = {"unknown":0}
        err = 0
        count = 0
        start_time = datetime.now()
        for node in dataJson:
            print count
            

            host = dataJson[node]['host']
            try:
                #info = self.ipdb.ip2loc(node["host"])
                if self.get_type(host) == IPv4:
                    info = self.ipdb.ip2loc(host)
                else:
                    info = self.ipdb.ipv6_2loc(host)
                print info
                if info:
                    if info[col].encode('ascii') in geo:
                        geo[info[col].encode('ascii')] += 1
                        try:
                            city[info["city"].encode('ascii')] += 1
                        except:
                            city[info["city"].encode('ascii')] = 1
                    else:
                        geo[info[col].encode('ascii')] = 1
                        city[info["city"].encode('ascii')] = 1
                else:
                    geo["unknown"] += 1
                    city["unknown"] += 1
            except Exception, errMsg:
                print "Err:", errMsg
                err += 1
            except KeyboardInterrupt:
                print ''
                self.saveNotAnalyzedNodes(dataJson, count, True)
                    
                break;
            if count == 200:
                break
            count += 1
        end_time = datetime.now()
        print "Duration:", end_time-start_time
        return geo, city, err
      
    def geoDistributionPeers(self, dataJson, col = "country_name"):
        geo = {"unknown":0}
        city = {"unknown":0}
        err = 0
        count = 0
        start_time = datetime.now()
        for infohash in dataJson:
            print count
            for peer in dataJson[infohash]["peers"]:
                print peer['addr'][0]
                host = peer['addr'][0]
                try:
                    #info = self.ipdb.ip2loc(node["host"])
                    if self.get_type(host) == IPv4:
                        info = self.ipdb.ip2loc(host)
                    else:
                        info = self.ipdb.ipv6_2loc(host)
                    print info
                    if info:
                        if info[col].encode('ascii') in geo:
                            geo[info[col].encode('ascii')] += 1
                            try:
                                city[info["city"].encode('ascii')] += 1
                            except:
                                city[info["city"].encode('ascii')] = 1
                        else:
                            geo[info[col].encode('ascii')] = 1
                            city[info["city"].encode('ascii')] = 1
                    else:
                        geo["unknown"] += 1
                        city["unknown"] += 1
                except Exception, errMsg:
                    print "Err:", errMsg
                    err += 1
                except KeyboardInterrupt:
                    print ''
                    self.saveNotAnalyzedNodes(dataJson, count, False)
                    break;
            count += 1
            
        end_time = datetime.now()
        print "Duration:", end_time-start_time
        return geo, city, err
        
        
    def saveNotAnalyzedNodes(self, nodes, count, bool_node):
        notAnalyzedNodes = {}
        count2 = 0
        for node in nodes:
            if count2 >= (count-1):
                notAnalyzedNodes[node] = nodes[node] 
            count2 += 1
            
        if bool_node:
            filename= "notAnalyzedNodes.json"
        else:
            filename= "notAnalyzedPeers.json"
        print "Saving not analyzed data into %s" % filename
        
        with open(filename, "w") as f:
            f.write(json.dumps(notAnalyzedNodes, ensure_ascii=False))
        f.close()    
        pass
   
def rawdata(f):
    """return the dict to the calling function without any processing."""
    dataJson = {}
    try: 
        f = open(f, 'rb')
        dataJson = json.loads( f.read() )
        f.close()
        #maybe delete file for better overview of analyzed files
    except:
        pass
    return dataJson
    


if __name__=="__main__":
    # The command line is in fix format, sorry for this.
    if len(sys.argv) < 2:
        print "Usage: %s logfile" % sys.argv[0]
        sys.exit(1)
    dataJson = rawdata(sys.argv[1])
    
    if "nodes" in sys.argv[1] or "Nodes" in sys.argv[1]:
        print "Zpracuji nodes"
        geo, city, err = Parser(sys.argv[1]).geoDistribution(dataJson)
    elif "peers" in sys.argv[1] or "Peers" in sys.argv[1]:
        print "zpracuji peery"
        geo, city, err = Parser(sys.argv[1]).geoDistributionPeers(dataJson)
    try:
        print '\nCountries:'
        for k, v in sorted(geo.items(), key=lambda x: -x[1]):
            print k,":",v
        print '\nCities:'
        for k, v in sorted(city.items(), key=lambda x: -x[1]):
            print k,":",v
        print err, "errors."
    except:
        pass
    pass
