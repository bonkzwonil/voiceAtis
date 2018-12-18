#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#==============================================================================
# voiceAtis - Reads an ATIS from IVAO using voice generation
# Copyright (C) 2018  Oliver Clemens
# 
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
# 
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
# 
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <https://www.gnu.org/licenses/>.
#==============================================================================

from __future__ import division

import os
import sys
import re
import time
import urllib
import urllib2
import gzip
from contextlib import closing
from math import floor
import warnings

reload(sys)  
sys.setdefaultencoding('iso-8859-15')  # @UndefinedVariable

# sys.path.insert(0,os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'python-metar'))

try:
    import pyttsx
    pyttsxImported = True
except ImportError:
    pyttsxImported = False
try:
    import pyuipc
    pyuipcImported = True
    debug = False
except ImportError:
        pyuipcImported = False
        debug = True
from metar.Metar import Metar

from aviationFormula import gcDistanceNm
from VaLogger import VaLogger


CHAR_TABLE = {'A' : 'APLHA',    'B' : 'BRAVO',      'C' : 'CHARLIE',
              'D' : 'DELTA',    'E' : 'ECHO',       'F' : 'FOXTROTT',
              'G' : 'GOLF',     'H' : 'HOTEL',      'I' : 'INDIA',
              'J' : 'JULIETT',  'K' : 'KILO',       'L' : 'LIMA',
              'M' : 'MIKE',     'N' : 'NOVEMBER',   'O' : 'OSCAR',
              'P' : 'PAPA',     'Q' : 'QUEBEC',     'R' : 'ROMEO',
              'S' : 'SIERRA',   'T' : 'TANGO',      'U' : 'UNIFORM',
              'V' : 'VICTOR',   'W' : 'WHISKEY',    'X' : 'XRAY',
              'Y' : 'YANKEE',   'Z' : 'ZULU'}



## Sperates integer Numbers with whitespace
# Needed for voice generation to be pronounced properly.
# Also replaces - by 'minus'
# Example: -250 > minus 2 5 0
def parseVoiceInt(number):
    if isinstance(number, float):
        number = int(number)
    if isinstance(number, int):
        number = str(number)
    
    numberSep = ''
    for k in number:
        if k != '-':
            numberSep = '{}{} '.format(numberSep,k)
        else:
            numberSep = '{}minus '.format(numberSep)
    return numberSep.strip()

## Sperates decimal Numbers with whitespace
# Also replaces . or , by 'decimal'
# Also replaces - by 'minus'
# Example: -118.80 > minus 1 1 8 decimal 8 0
def parseVoiceFloat(number):
    if isinstance(number, float):
        number = str(number)
    
    numberSep = ''
    for k in number:
        if k != '.' and k != ',' and k!= '-':
            numberSep = '{}{} '.format(numberSep,k)
        elif k != '-':
            numberSep = '{}decimal '.format(numberSep)
        else:
            numberSep = '{}minus '.format(numberSep)
    return numberSep.strip()

## Search a string for numbers and seperate with whitespaces.
# Using parseVoiceInt() and parseVoiceFloat().
def parseVoiceString(string):
    pattern = re.compile('\d+[,.]\d+')
    match = pattern.search(string)
    while match is not None:
        replaceStr = parseVoiceFloat(string[match.start():match.end()])
        string = '{}{}{}'.format(string[0:match.start()],replaceStr,string[match.end():])
        match = pattern.search(string)
        
    pattern = re.compile('\d\d+')
    match = pattern.search(string)
    while match is not None:
        replaceStr = parseVoiceInt(string[match.start():match.end()])
        string = '{}{}{}'.format(string[0:match.start()],replaceStr,string[match.end():])
        match = pattern.search(string)
        
    return string

## Splits a string at each char and replaces them with ICAO-alphabet.
def parseVoiceChars(string):
        
    stringSep = ''
    for k in string:
        stringSep = '{}{} '.format(stringSep,CHAR_TABLE[k])
    
    return stringSep.strip()


class VoiceAtis(object):
    
    STATION_SUFFIXES = ['TWR','APP','GND','DEL','DEP']
    
    SPEECH_RATE = 150
    
    SLEEP_TIME = 3 # s
    
    RADIO_RANGE = 180 # nm
    
    OFFSETS = [(0x034E,'H'),    # com1freq
               (0x3118,'H'),    # com2freq
               (0x3122,'b'),    # radioActive
               (0x0560,'l'),    # ac Latitude
               (0x0568,'l'),    # ac Longitude
              ]
    
    WHAZZUP_URL = 'http://api.ivao.aero/getdata/whazzup/whazzup.txt.gz'
    WHAZZUP_METAR_URL = 'http://wx.ivao.aero/metar.php'
    
    OUR_AIRPORTS_URL = 'http://ourairports.com/data/'
    

    COM1_FREQUENCY_DEBUG = 199.99
    
    # EDDS
#     COM2_FREQUENCY_DEBUG = 126.12
#     LAT_DEBUG = 48.687
#     LON_DEBUG = 9.205

    # EDDM
#     COM2_FREQUENCY_DEBUG = 123.12
#     LAT_DEBUG = 48.353
#     LON_DEBUG = 11.786

    # LIRF
    COM2_FREQUENCY_DEBUG = 121.85
    LAT_DEBUG = 41.8
    LON_DEBUG = 12.2
    
    # LIBR
    COM2_FREQUENCY_DEBUG = 121.85
    LAT_DEBUG = 41.8
    LON_DEBUG = 12.2


    WHAZZUP_TEXT_DEBUG = r'H:\My Documents\Sonstiges\voiceAtis\whazzup_1.txt'
    
    ## Setup the VoiceAtis object.
    # Also starts the voice generation loop.
    def __init__(self,**optional):
        #TODO: Test switching of frequency properly.
        #TODO: Remove the debug code when tested properly.
        #TODO: Improve logged messages.
        #TODO: Create GUI.
        
        # Process optional arguments.
        self.debug = optional.get('Debug',debug)
        
        # Get file path.
        self.rootDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Init logging.
        self.logger = VaLogger(os.path.join(self.rootDir,'logs'))
        
        # First log message.
        self.logger.info('voiceAtis started')
        
        # Establish pyuipc connection
        while True:
            try:
                self.pyuipcConnection = pyuipc.open(0)
                self.pyuipcOffsets = pyuipc.prepare_data(self.OFFSETS)
                self.logger.info('FSUIPC connection established.')
                break
            except NameError:
                self.pyuipcConnection = None
                self.logger.warning('Using voiceAtis without FSUIPC.')
                break
            except:
                self.logger.warning('No Sim detected. Start your Sim first. Retrying in 20 seconds.')
                time.sleep(20)
        
        
        # Read file with airport frequencies and coordinates.
        self.getAirportData()
        
        # Show debug Info
        #TODO: Remove for release.
        if self.debug:
            self.logger.info('Debug mode on.')
            self.logger.setLevel(ConsoleLevel='debug')
        
        # Infinite loop.
        try:
            while True:
                
                # Get ATIS frequency and associated airport.
                self.getPyuipcData()
                
                # Get best suitable Airport.
                self.getAirport()
                
                # Handle if no airport found.
                if self.airport is None:
                    self.logger.info('No airport found, sleeping for {} seconds...'.format(self.SLEEP_TIME))
                    time.sleep(self.SLEEP_TIME)
                    continue
                else:
                    self.logger.info('Airport: {}.'.format(self.airport))
                
                # Get whazzup file
                if not self.debug:
                    self.getWhazzupText()
                else:
                    self.getWhazzupTextDebug()
                
                # Read whazzup text and get a station.
                self.parseWhazzupText()
                
                # Check if station online.
                if self.atisRaw is not None:
                    self.logger.info('Station found, decoding Atis.')
                else:
                    # Actions, if no station online.
                    self.logger.info('No station online, using metar only.')
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        self.metar = Metar(self.getAirportMetar(),strict=False)
                    
                    self.parseVoiceMetar()
                    
                    # Parse atis voice with metar only.
                    self.atisVoice = '{}, {}.'.format(self.airportInfos[self.airport][3],self.metarVoice)
                    
                    # Read the metar.
                    self.readVoice()
                    
                    time.sleep(self.SLEEP_TIME)
                    continue
                
                # Parse ATIS.
                # Information.
                self.getInfoIdentifier()
                self.parseVoiceInformation()
                
                # Metar.
                if not self.ivac2:
                    self.parseMetar(self.atisRaw[2].strip())
                else:
                    for ar in self.atisRaw:
                        if ar.startswith('METAR'):
                            self.parseMetar(ar.replace('METAR ','').strip())
                            break
                
                self.parseVoiceMetar()
                
                # Runways / TRL / TA
                self.parseRawRwy()
                self.parseVoiceRwy()
                
                # comment.
                self.parseVoiceComment()
                
                # Compose complete atis voice string.
                self.atisVoice = '{} {} {} {} Information {}, out.'.format(self.informationVoice,self.metarVoice,self.rwyVoice,self.commentVoice,self.informationIdentifier)
                
                # Read the string.
                self.readVoice()
                
                pass
                
        except KeyboardInterrupt:
            # Actions at Keyboard Interrupt.
            self.logger.info('Loop interrupted by user.')
            if pyuipcImported:
                self.pyuipc.close()
            
    
    
    ## Downloads and reads the whazzup from IVAO 
    def getWhazzupText(self):
        urllib.urlretrieve(self.WHAZZUP_URL, 'whazzup.txt.gz')
        with gzip.open('whazzup.txt.gz', 'rb') as f:
            self.whazzupText = f.read().decode('iso-8859-15')
        os.remove('whazzup.txt.gz')
    
    
    ## Reads a whazzup file on disk.
    # For debug purposes.
    def getWhazzupTextDebug(self):
        with open(self.WHAZZUP_TEXT_DEBUG) as whazzupFile:
            self.whazzupText = whazzupFile.read()
        pass
    
    
    ## Find a station of the airport and read the ATIS string.
    def parseWhazzupText(self):
        # Find an open station
        for st in self.STATION_SUFFIXES:
            matchObj = re.search('{}\w*?_{}'.format(self.airport,st),self.whazzupText)
            
            if matchObj is not None:
                break
        
        if matchObj is not None:
            # Extract ATIS.
            lineStart = matchObj.start()
            lineEnd = self.whazzupText.find('\n',matchObj.start())
            stationInfo = self.whazzupText[lineStart:lineEnd].split(':')
            self.ivac2 = bool(int(stationInfo[39][0]) - 1)
            self.atisTextRaw = stationInfo[35].encode('iso-8859-15')
            self.atisRaw = stationInfo[35].encode('iso-8859-15').split('^§')
        else:
            self.atisRaw = None
    
    
    def parseMetar(self,metarString):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.metar = Metar(metarString,strict=False)
    
    
    ## Parse runway and transition data.
    # Get active runways for arrival and departure.
    # Get transistion level and altitude.
    def parseRawRwy(self):
        self.rwyInformation = [None,None,None,None]
        if not self.ivac2:
            strSplit = self.atisRaw[3].split(' / ')

            for sp in strSplit:
                # ARR.
                if sp[0:3] == 'ARR':
                    self.rwyInformation[0] = []
                    arr = sp.replace('ARR RWY ','').strip()
                    starts = []
                    for ma in re.finditer('\d{2}[RLC]?',arr):
                        starts.append(ma.start())
                    for st in range(len(starts)):
                        if st < len(starts)-1:
                            rwy = arr[starts[st]:starts[st+1]]
                        else:
                            rwy = arr[starts[st]:]
                        curRwy = [rwy[0:2],None,None,None]
                        if 'L' in rwy:
                            curRwy[1] = 'Left'
                        if 'C' in rwy:
                            curRwy[2] = 'Center'
                        if 'R' in rwy:
                            curRwy[3] = 'Right'
                        self.rwyInformation[0].append(curRwy)
                
                # DEP.
                elif sp[0:3] == 'DEP':
                    self.rwyInformation[1] = []
                    dep = sp.replace('DEP RWY ','').strip()
                    starts = []
                    for ma in re.finditer('\d{2}[RLC]?',dep):
                        starts.append(ma.start())
                    for st in range(len(starts)):
                        if st < len(starts)-1:
                            rwy = dep[starts[st]:starts[st+1]]
                        else:
                            rwy = dep[starts[st]:]
                        curRwy = [rwy[0:2],None,None,None]
                        if 'L' in rwy:
                            curRwy[1] = 'Left'
                        if 'C' in rwy:
                            curRwy[2] = 'Center'
                        if 'R' in rwy:
                            curRwy[3] = 'Right'
                        self.rwyInformation[1].append(curRwy)
                        
                # TRL/TA
                elif sp[0:3] == 'TRL':
                    self.rwyInformation[2] = sp.strip().replace('TRL FL','')
                    
                elif sp[0:2] == 'TA':
                    self.rwyInformation[3] = sp.strip().replace('TA ','').replace('FT','')
        # Ivac 2
        else:
            for ar in self.atisRaw:
                if ar.startswith('TA'):
                    trlTaSplit = ar.split(' / ')
                    self.rwyInformation[3] = trlTaSplit[0].replace('TA ','')
                    self.rwyInformation[2] = trlTaSplit[1].replace('TRL','')
                    
                elif ar.startswith('ARR'):
                    curRwy = [ar[8:10],None,None,None]
                    if 'L' in ar[8:]:
                        curRwy[1] = 'Left'
                    if 'C' in ar[8:]:
                        curRwy[2] = 'Center'
                    if 'R' in ar[8:]:
                        curRwy[3] = 'Right'
                    if self.rwyInformation[0] is None:
                        self.rwyInformation[0] = [curRwy]
                    else:
                        self.rwyInformation[0].append(curRwy)
                        
                elif ar.startswith('DEP'):
                    curRwy = [ar[8:10],None,None,None]
                    if 'L' in ar[8:]:
                        curRwy[1] = 'Left'
                    if 'C' in ar[8:]:
                        curRwy[2] = 'Center'
                    if 'R' in ar[8:]:
                        curRwy[3] = 'Right'
                    if self.rwyInformation[1] is None:
                        self.rwyInformation[1] = [curRwy]
                    else:
                        self.rwyInformation[1].append(curRwy)
    
    ## Generate a string of the metar for voice generation.
    def parseVoiceMetar(self):
        self.metarVoice = 'Met report'
        
        # Time
        hours = parseVoiceInt('{:02d}'.format(self.metar._hour))
        minutes = parseVoiceInt('{:02d}'.format(self.metar._min))
        self.metarVoice = '{} time {} {} zulu'.format(self.metarVoice,hours,minutes)
        
        # Wind
        if self.metar.wind_speed._value != 0:
            if self.metar.wind_dir is not None:
                self.metarVoice = '{}, wind {}, {}'.format(self.metarVoice,parseVoiceString(self.metar.wind_dir.string()),parseVoiceString(self.metar.wind_speed.string()))
            else:
                self.metarVoice = '{}, wind variable, {}'.format(self.metarVoice,parseVoiceString(self.metar.wind_speed.string()))
        else:
            self.metarVoice = '{}, wind calm'.format(self.metarVoice,self.metar.wind_dir.string(),self.metar.wind_speed.string())
        
        if self.metar.wind_gust is not None:
            self.metarVoice = '{}, maximum {}'.format(self.metarVoice,parseVoiceString(self.metar.wind_gust.string()))
        
        if self.metar.wind_dir_from is not None:
            self.metarVoice = '{}, variable between {} and {}'.format(self.metarVoice,parseVoiceString(self.metar.wind_dir_from.string()),parseVoiceString(self.metar.wind_dir_to.string()))
            
        
        # Visibility.
        #TODO: implement directions
        self.metarVoice = '{}, visibility {}'.format(self.metarVoice,self.metar.vis.string())
        
        # runway visual range
        rvr = self.metar.runway_visual_range().replace(';', ',')
        if rvr:
            rvrNew = ''
            lastEnd = 0
            rvrPattern = re.compile('[0123]\d[LCR]?(?=,)')
            for ma in rvrPattern.finditer(rvr):
                rwyRaw = rvr[ma.start():ma.end()]
                rwyStr = parseVoiceInt(rwyRaw[0:2])
                if len(rwyRaw) > 2:
                    if rwyRaw[2] == 'L':
                        rwyStr = '{} left'.format(rwyStr)
                    elif rwyRaw[2] == 'C':
                        rwyStr = '{} center'.format(rwyStr)
                    elif rwyRaw[2] == 'R':
                        rwyStr = '{} right'.format(rwyStr)
                rvrNew = '{}{}{}'.format(rvrNew,rvr[lastEnd:ma.start()],rwyStr)
                lastEnd = ma.end()
            
            rvrNew = '{}{}'.format(rvrNew,rvr[lastEnd:])
            
            self.metarVoice = '{}, visual range {}'.format(self.metarVoice,rvrNew)
        
        # weather phenomena
        if self.metar.weather:
            self.metarVoice = '{}, {}'.format(self.metarVoice,self.metar.present_weather().replace(';',','))
        
        # clouds
        if self.metar.sky:
            self.metarVoice = '{}, {}'.format(self.metarVoice,self.metar.sky_conditions(',').replace(',',', ').replace('a few','few'))
        elif 'CAVOK' in self.metar.code:
            self.metarVoice = '{}, clouds and visibility ok'.format(self.metarVoice)
        
        
        # runway condition
        #TODO: Implement runway conditions
        # Not implemented in python-metar
        
        # temperature
        tempValue = parseVoiceInt(str(int(self.metar.temp._value)))
        if self.metar.temp._units == 'C':
            tempUnit = 'degree Celsius'
        else:
            tempUnit = 'degree Fahrenheit'
            
        self.metarVoice = '{}, temperature {} {}'.format(self.metarVoice,tempValue,tempUnit)
        
        # dew point
        dewptValue = parseVoiceInt(str(int(self.metar.dewpt._value)))
        if self.metar.dewpt._units == 'C':
            dewptUnit = 'degree Celsius'
        else:
            dewptUnit = 'degree Fahrenheit'
            
        self.metarVoice = '{}, dew point {} {}'.format(self.metarVoice,dewptValue,dewptUnit)
        
        # QNH
        if self.metar.press._units == 'MB':
            pressValue = parseVoiceInt(str(int(self.metar.press._value)))
            self.metarVoice = '{}, Q N H {} hectopascal'.format(self.metarVoice,pressValue)
        else:
            self.metarVoice = '{}, Altimeter {}'.format(self.metarVoice,parseVoiceString(self.metar.press.string()))
        
        #TODO: implement trend
        
        self.metarVoice = '{},'.format(self.metarVoice)
    
    ## Generate a string of the information identifier for voice generation.
    def parseVoiceInformation(self):
        if not self.ivac2:
            timeMatch = re.search(r'\d{4}z',self.atisRaw[1])
            startInd = timeMatch.start()
            endInd = timeMatch.end()- 1
            timeStr = parseVoiceInt(self.atisRaw[1][startInd:endInd])
            
            self.informationVoice = '{} {} Zulu.'.format(self.atisRaw[1][0:startInd-1],timeStr)
        
        else:
            information = self.atisRaw[1].split(' ')
            airport = information[0]
            airport = self.airportInfos[airport][3]
            time = parseVoiceInt(information[4][0:4])
            
            self.informationVoice = '{} Information {} recorded at {} Zulu.'.format(airport,self.informationIdentifier,time)
    
    
    ## Generate a string of the runway information for voice generation.
    def parseVoiceRwy(self):
        self.rwyVoice = ''
        
        # ARR.
        if self.rwyInformation[0] is not None:
            self.rwyVoice = '{}Arrival runway '.format(self.rwyVoice)
            for arr in self.rwyInformation[0]:
                if arr[1:4].count(None) == 3:
                    self.rwyVoice = '{}{} and '.format(self.rwyVoice,parseVoiceInt(arr[0]))
                else:
                    for si in arr[1:4]:
                        if si is not None:
                            self.rwyVoice = '{}{} {} and '.format(self.rwyVoice,parseVoiceInt(arr[0]),si)
            self.rwyVoice = '{},'.format(self.rwyVoice[0:-5])
        
        # DEP.
        if self.rwyInformation[1] is not None:
            self.rwyVoice = '{} Departure runway '.format(self.rwyVoice)
            for dep in self.rwyInformation[1]:
                if dep[1:4].count(None) == 3:
                    self.rwyVoice = '{}{} and '.format(self.rwyVoice,parseVoiceInt(dep[0]))
                else:
                    for si in dep[1:4]:
                        if si is not None:
                            self.rwyVoice = '{}{} {} and '.format(self.rwyVoice,parseVoiceInt(dep[0]),si)
            self.rwyVoice = '{}, '.format(self.rwyVoice[0:-5])
        
        # TRL
        if self.rwyInformation[2] is not None:
            self.rwyVoice = '{}Transition level {}, '.format(self.rwyVoice,parseVoiceInt(self.rwyInformation[2]))
        
        # TA
        if self.rwyInformation[3] is not None:
            self.rwyVoice = '{}Transition altitude {} feet,'.format(self.rwyVoice,self.rwyInformation[3])
            
    ## Generate a string of ATIS comment for voice generation.
    def parseVoiceComment(self):
        if not self.ivac2:
            self.commentVoice = '{},'.format(parseVoiceString(self.atisRaw[4]))
        else:
            self.commentVoice = ''
    
    ## Reads the atis string using voice generation.
    def readVoice(self):
        # Init currently Reading with None.
        self.currentlyReading = [None,None]
        
        self.logger.debug('Voice Text is: {}'.format(self.atisVoice))
        
        if pyttsxImported:
            # Set properties currently reading
            self.currentlyReading[0] = self.airport
            self.currentlyReading[1] = self.com2frequency
            
            # Init voice engine.
            self.engine = pyttsx.init()
               
            # Set properties.
            voices = self.engine.getProperty('voices')
            for vo in voices:
                if 'english' in vo.name.lower():
                    self.engine.setProperty('voice', vo.id)
                    self.logger.debug('Using voice: {}'.format(vo.name))
                    break
            
            self.engine.setProperty('rate', self.SPEECH_RATE)
             
            # Start listener and loop.
            self.engine.connect('started-word', self.onWord)

            # Say complete ATIS
            self.engine.say(self.atisVoice)
            self.logger.info('Start reading.')
            self.engine.runAndWait()
            self.logger.info('Reading finished.')
            self.engine = None
            
        else:
            self.logger.warning('Speech engine not initalized, no reading. Sleeping for {} seconds...'.format(self.SLEEP_TIME))
            time.sleep(self.SLEEP_TIME)
    
    ## Callback for stop of reading.
    # Stops reading if frequency change/com deactivation/out of range.
    def onWord(self, name, location, length):  # @UnusedVariable
        self.getPyuipcData()
        
        com1Reading = self.com1frequency == self.currentlyReading[1] and self.com1active
        com2Reading = self.com2frequency == self.currentlyReading[1] and self.com2active
        #TODO: Implement stop if too far away.
        
        if not com1Reading and not com2Reading:
            self.engine.stop()
            self.currentlyReading = [None,None]
    
    
    ## Reads current frequency and COM status.
    def getPyuipcData(self):
        
        if pyuipcImported:
            results = pyuipc.read(self.pyuipcOffsets)
        
            # frequency
            hexCode = hex(results[0])[2:]
            self.com1frequency = float('1{}.{}'.format(hexCode[0:2],hexCode[2:]))
            hexCode = hex(results[1])[2:]
            self.com2frequency = float('1{}.{}'.format(hexCode[0:2],hexCode[2:]))
            
            # radio active
            #TODO: Test accuracy of this data (with various planes and sims)
            radioActiveBits = list(map(int, '{0:08b}'.format(results[2])))
            if radioActiveBits[2]:
                self.com1active = True
                self.com2active = True
            elif radioActiveBits[0]:
                self.com1active = True
                self.com2active = False
            elif radioActiveBits[1]:
                self.com1active = False
                self.com2active = True
            else:
                self.com1active = False
                self.com2active = False
            
            # lat lon
            self.lat = results[3] * (90.0/(10001750.0 * 65536.0 * 65536.0))
            self.lon = results[4] * (360.0/(65536.0 * 65536.0 * 65536.0 * 65536.0))
        
        else:
            self.com1frequency = self.COM1_FREQUENCY_DEBUG
            self.com2frequency = self.COM2_FREQUENCY_DEBUG
            self.com1active = True
            self.com2active = True
            self.lat = self.LAT_DEBUG
            self.lon = self.LON_DEBUG
        
        # Logging.
        if self.com1active:
            com1activeStr = 'active'
        else:
            com1activeStr = 'inactive'
        if self.com2active:
            com2activeStr = 'active'
        else:
            com2activeStr = 'inactive'
        
        self.logger.debug('COM 1: {} ({}), COM 2: {} ({})'.format(self.com1frequency,com1activeStr,self.com2frequency,com2activeStr))
#         self.logger.debug('COM 1 active: {}, COM 2 active: {}'.format(self.com1active,self.com2active))
    
    ## Determine if there is an airport aplicable for ATIS reading.
    def getAirport(self):
        self.airport = None
        frequencies = []
        if self.com1active:
            frequencies.append(self.com1frequency)
        if self.com2active:
            frequencies.append(self.com2frequency)
            
        if frequencies:
            distanceMin = self.RADIO_RANGE + 1
            for ap in self.airportInfos:
                distance = gcDistanceNm(self.lat, self.lon, self.airportInfos[ap][1], self.airportInfos[ap][2])
                if (floor(self.airportInfos[ap][0]*100)/100) in frequencies and distance < self.RADIO_RANGE and distance < distanceMin:
                    distanceMin = distance
                    self.airport = ap
    
    
    ## Read data of airports from a given file.
    def getAirportDataFile(self,apFile):
        with open(apFile) as aptInfoFile:
            for li in aptInfoFile:
                lineSplit = re.split('[,;]',li)
                if not li.startswith('#') and len(lineSplit) == 5:
                    self.airportInfos[lineSplit[0].strip()] = (float(lineSplit[1]),float(lineSplit[2]),float(lineSplit[3]),lineSplit[4].replace('\n',''))
    
    ## Read data of airports from http://ourairports.com.
    def getAirportDataWeb(self):
        
        airportFreqs = {}
        
        # Read the file with frequency.
        with closing(urllib2.urlopen(self.OUR_AIRPORTS_URL + 'airport-frequencies.csv', timeout=5)) as apFreqFile:
            for li in apFreqFile:
                lineSplit = li.split(',')
                if lineSplit[3] == '"ATIS"':
                    airportFreqs[lineSplit[2].replace('"','')] = float(lineSplit[-1].replace('\n',''))
        
        # Read the file with other aiport data.
        # Add frequency and write them to self. airportInfos.
        with closing(urllib2.urlopen(self.OUR_AIRPORTS_URL + 'airports.csv')) as apFile:
            for li in apFile:
                lineSplit = re.split((",(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)"),li)
                    
                apCode = lineSplit[1].replace('"','')
                if apCode in airportFreqs and len(apCode) <= 4:
                    apFreq = airportFreqs[apCode]
                    if 100.0 < apFreq < 140.0:
                        self.airportInfos[apCode] = [apFreq,float(lineSplit[4]),float(lineSplit[5]),lineSplit[3].replace('"','')]
        
        
    ## Reads airportData from two sources.
    def getAirportData(self):
        self.airportInfos = {}
        
        try:
            # Try to read airport data from web.
            self.getAirportDataWeb()
            self.getAirportDataFile(os.path.join(self.rootDir,'airports_add.info'))
            collectedFromWeb = True
            
        except:
            # If this fails, use the airports from airports.info.
            self.logger.warning('Unable to get airport data from web. Using airports.info. Error: {}'.format(sys.exc_info()[0]))
            self.airportInfos = {}
            collectedFromWeb = False
            try:
                self.getAirportDataFile(os.path.join(self.rootDir,'airports.info'))
            except:
                self.logger.error('Unable to read airport data from airports.info!')
        
        # Sort airportInfos and write them to a file for future use if collected from web.
        if collectedFromWeb:
            apInfoPath = os.path.join(self.rootDir,'airports.info')
            apList = self.airportInfos.keys()
            apList.sort()
            with open(apInfoPath,'w') as apDataFile:
                for ap in apList:
                    apDataFile.write('{:>4}; {:6.2f}; {:11.6f}; {:11.6f}; {}\n'.format(ap,self.airportInfos[ap][0],self.airportInfos[ap][1],self.airportInfos[ap][2],self.airportInfos[ap][3]))
    
    
    ## Determines the info identifier of the loaded ATIS.
    def getInfoIdentifier(self):
        if not self.ivac2:
            informationPos = re.search('information ',self.atisRaw[1]).end()
            informationSplit = self.atisRaw[1][informationPos:].split(' ')
            self.informationIdentifier = informationSplit[0]
        else:
            self.informationIdentifier = CHAR_TABLE[re.findall(r'(?<=ATIS )[A-Z](?= \d{4})',self.atisRaw[1])[0]]
        
    
    ## Retrieves the metar of an airport independet of an ATIS.
    def getAirportMetar(self):
        
        if not debug:
            urllib.urlretrieve(self.WHAZZUP_METAR_URL, 'whazzup_metar.txt')
            
        with open('whazzup_metar.txt', 'r') as metarFile:
            metarText = metarFile.read()
            
        if not debug:
            os.remove('whazzup_metar.txt')
        
        metarStart = metarText.find(self.airport)
        metarEnd = metarText.find('\n',metarStart)
        
        return metarText[metarStart:metarEnd]
    
    
if __name__ == '__main__':
    voiceAtis = VoiceAtis()
    pass
