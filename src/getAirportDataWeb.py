#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#==============================================================================
# getAirportDataWeb - Reads airport data from http://ourairports.com
# Copyright (C) 2018  Oliver Clemens
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#==============================================================================

from __future__ import division

import os
import re
import urllib2

AP_URL = 'http://ourairports.com/data/airports.csv'
AP_FREQ_URL = 'http://ourairports.com/data/airport-frequencies.csv'

apInfoPath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'airports.info')
airports = {}
airportFreqs = {}

with urllib2.urlopen(AP_FREQ_URL) as apFreqFile:
    for li in apFreqFile:
        lineSplit = li.split(',')
        if lineSplit[3] == '"ATIS"':
            airportFreqs[lineSplit[2].replace('"','')] = float(lineSplit[-1].replace('\n',''))

with urllib2.urlopen(AP_URL) as apFile:
    for li in apFile:
        lineSplit = re.split((",(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)"),li)
            
        apCode = lineSplit[1].replace('"','')
        if apCode in airportFreqs and len(apCode) <= 4:
            apFreq = airportFreqs[apCode]
            if 100.0 < apFreq < 140.0:
                airports[apCode] = [apFreq,float(lineSplit[4]),float(lineSplit[5]),lineSplit[3].replace('"','')]
            
apList = airports.keys()
apList.sort()
with open(apInfoPath,'w') as apDataFile:
    for ap in apList:
        apDataFile.write('{:>4}, {:6.2f}, {:11.6f}, {:11.6f}, {}\n'.format(ap,airports[ap][0],airports[ap][1],airports[ap][2],airports[ap][3]))