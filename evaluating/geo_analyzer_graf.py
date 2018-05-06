#!/usr/bin/python
# 


# This script was created by David Bezdek for purpose of a master
# thesis 
# David Bezdek, xbezde11@stud.fit.vutbr.cz
# Faculty of Information Technology, Brno University of Technology
# 2018.05.23

# reading text outputs of 



import os
import operator


class Parser(object):
    def __init__(self, dup = "-id"):
        self.countriesPool = {}
        self.citiesPool = {}
        self.countries = False
        self.cities = False
        pass

    def readFile(self, name):
        f = open(name, 'r')
        for line in f.readlines():
            if 'Duration' in line:
                print line
            elif 'Countries' in line:
                self.countries = True
                print "nastavuju countires"
            elif 'Cities' in line:
                self.countries = False
                print "nastavuju cities"
                self.cities = True
            elif len(line) > 2: #eliminate empty lines
                line = line.split('\r\n')
                line = line[0].split(':')
                #print line
                if self.countries:
                    #print "pude do countr"
                    country = line[0]
                    if country in self.countriesPool:
                        self.countriesPool[country] += int(line[1])
                    else:
                        try:
                            self.countriesPool[country] = int(line[1])
                        except Exception, err:
                            print err
                elif self.cities:
                    #print "pude do countr"
                    city = line[0]
                    if city in self.citiesPool:
                        self.citiesPool[city] += int(line[1])
                    else:
                        try:
                            self.citiesPool[city] = int(line[1])
                        except Exception, err:
                            print err
                
        f.close()
            
        pass

if __name__=="__main__":
   
    parser = Parser()
    for name in os.listdir("."):
        if 'mereni' in name:
            print name
            parser.readFile(name)
            
    peers = 0        
    print "Countries:"
    sorted_x = sorted(parser.countriesPool.items(), key=operator.itemgetter(1))
    for key, value in sorted_x:
        if value > 2:
            print "%s: %i" % ( key, value)
            peers += value 
    
    print "\n\nCities:"
    sorted_y = sorted(parser.citiesPool.items(), key=operator.itemgetter(1))
    for key, value in sorted_y:
        if value > 2:
            print "%s: %i" % ( key, value)
    #for key in parser.citiesPool:
    #    print key + ":" + parser.citiesPool[key]
    print "Total amount of peers: %i" % peers 
    pass
