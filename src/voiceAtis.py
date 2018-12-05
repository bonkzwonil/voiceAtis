#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#==============================================================================
# voiceAtis - Reads an ATIS from IVAO using voice generation
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
# 
#==============================================================================
# CHANGELOG
#
# version 0.0.2 - 05.12.2018
# - implemented wind gusts and variable wind
# - added pyuipc (untested)
# - added logic to get airport
# 
# version 0.0.1 - 03.12.2018
# - first version for testing purposes
# - some Atis feartures missing
# - no pyuipc
# - voice not tested
# 
#==============================================================================
# ROADMAP
# 
# - running version
# - get ivac2 atis running
# 
#==============================================================================

import os
import re
import time
import urllib.request
import gzip

try:
    import pyttsx3
    pyttsx3Imported = True
except ImportError:
    print('No voice')
    pyttsx3Imported = False
try:
    import pyuipc  # @UnusedImport
    pyuipcImported = True
except ImportError:
        print('No pyuipc')
        pyuipcImported = False
from metar.Metar import Metar

import avFormula

## Sperate Numbers with whitespace
# Needed for voice generation to be pronounced properly.
# Example: 250 > 2 5 0
def parseVoiceInt(number):
    if isinstance(number, float):
        number = int(number)
    if isinstance(number, int):
        number = str(number)
    
    numberSep = ''
    for k in number:
        numberSep = '{}{} '.format(numberSep,k)
    return numberSep.strip()

## Sperate Numbers with whitespace and replace . by decimal'
def parseVoiceFloat(number):
    if isinstance(number, float):
        number = str(number)
    
    numberSep = ''
    for k in number:
        if k != '.' and k != ',':
            numberSep = '{}{} '.format(numberSep,k)
        else:
            numberSep = '{}decimal '.format(numberSep,k)
    return numberSep.strip()

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

class VoiceAtis(object):
    
    ENGLISH_VOICE = u'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0'
    GERMAN_VOICE = u'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_DE-DE_HEDDA_11.0'
    STATION_SUFFIXES = ['TWR','APP','GND','DEL','DEP']
    
    SPEECH_RATE = 140
    
    #TODO: reduce to normal time when finished debug
    SLEEP_TIME = 30         # s
    
    DISTANCE_THRESHOLD = 30 # nm
    
    OFFSETS = [(0x034E,'H'),    # com1freq
               (0x3118,'H'),    # com2freq
               (0x3122,'b'),    # radioActive
               (0x6D90,'f'),    # lat
               (0x6D98,'f'),    # lon
              ]
    
    DEBUG = True
#     COM1_FREQUENCY_DEBUG = 123.12 # EDDM_ATIS
    COM1_FREQUENCY_DEBUG = 199.99
    COM2_FREQUENCY_DEBUG = 126.12 # EDDS_ATIS
    LAT_DEBUG = 48.353
    LON_DEBUG = 11.786
    WHAZZUP_TEXT_DEBUG = r'H:\My Documents\Sonstiges\voiceAtis\whazzup_1.txt'
    
    ## Setup the VoiceAtis object.
    # Also starts the voice generation loop.
    def __init__(self):
        #TODO: Add FSUIPC code to get ATIS frequency
        
        self.srcDir = os.path.dirname(os.path.abspath(__file__))
        
        self.currentlyReading = [None,None]
        
        if pyuipcImported:
            self.pyuipcConnection = pyuipc.open(0)
            self.pyuipcOffsets = pyuipc.prepare_data(self.OFFSETS)
        else:
            self.pyuipcConnection = None
            
        self.getAirportInfos()
        
        if self.DEBUG:
            print('Debug')
        
        # Infinite loop.
        try:
            while True:
                
                # Get ATIS frequency and associated airport.
                self.getPyuipcData()
                
                # Get best suitable Airport.
                self.getAirport()
                
                if self.airport is None:
                    print('No airport found, sleeping for {} seconds...'.format(self.SLEEP_TIME))
                    time.sleep(self.SLEEP_TIME)
                    continue
                
                # Get whazzup file
                if not self.DEBUG:
                    self.getWhazzupText()
                else:
                    self.getWhazzupTextDebug()
                
                # Read whazzup text and get a station.
                self.parseWhazzupText()
                
                if self.atisRaw is None:
                    print('No station online, sleeping for {} seconds...'.format(self.SLEEP_TIME))
                
                ####### DEBUG #######
                if self.DEBUG:
                    self.atisRaw[2] = 'EDDL 212150Z 06007KT 4000 W2000 OVC010 02/01 Q1005 R23L/190195 R23R/190195 TEMPO BKN008'
#                     self.atisRaw[2] = 'KMIA 041253Z 21004KT 10SM FEW015 FEW050 FEW085 BKN250 24/24 A3004 RMK AO2 SLP171 T02440244'
#                     self.atisRaw[2] = 'METAR KEWR 111851Z VRB03G19KT 2SM R04R/3000VP6000FT TSRA BR FEW015 BKN040CB BKN065 OVC200 22/22 A2987'
#                     self.atisRaw[2] = 'METAR KEWR 111851Z 25003G19KT 210V290 2SM R04R/3000VP6000FT R04L/0225U TSRA BR FEW015 BKN040CB BKN065 OVC200 22/22 A2987'
                ##### DEBUG END #####
                
                # Parse ATIS.
                if not self.ivac2:
                    # Information.
                    self.informationVoice = self.parseVoiceInformation()
                    
                    # Metar.
                    self.metar = Metar(self.atisRaw[2].strip(),strict=False)
                    
                    # Runways / TRL / TA
                    self.parseRawRwy1()
                    self.parseVoiceRwy()
                
                    # Parse voice.
                    self.parseVoiceMetar()
                
                    atisVoice = '{}. {}. {}'.format(self.informationVoice,self.metarVoice,self.rwyVoice)
                    
                    print(self.atisRaw)
                    print(atisVoice)
                
    #             self.readVoice()
                
                # Wait some time for performance reasons.
                time.sleep(self.SLEEP_TIME)
        except KeyboardInterrupt:
            if pyuipcImported:
                self.pyuipc.close()    
    
    
    ## Downloads and reads the whazzup from IVAO 
    def getWhazzupText(self):
        urllib.request.urlretrieve('http://api.ivao.aero/getdata/whazzup/whazzup.txt.gz', 'whazzup.txt.gz')
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
        
        if matchObj is None:
            self.atisRaw = None
        
        # Extract ATIS.
        lineStart = matchObj.start()
        lineEnd = self.whazzupText.find('\n',matchObj.start())
        stationInfo = self.whazzupText[lineStart:lineEnd].split(':')
        self.ivac2 = bool(int(stationInfo[39][0]) - 1)
        self.atisRaw = stationInfo[35].split('^�')
    
    
    ## Parse runway and transition data.
    # Get active runways for arrival and departure.
    # Get transistion level and altitude.
    def parseRawRwy1(self):
        strSplit = self.atisRaw[3].split(' / ')
        
        self.rwyInformation = [None,None,None,None]
        
        for sp in strSplit:
            if sp[0:3] == 'ARR':
                arr = sp.replace('ARR RWY ','').strip().split(' ')
                self.rwyInformation[0] = []
                for rwy in arr:
                    curRwy = [rwy[0:2],None,None,None]
                    if 'L' in rwy:
                        curRwy[1] = 'Left'
                    if 'C' in rwy:
                        curRwy[2] = 'Center'
                    if 'R' in rwy:
                        curRwy[3] = 'Right'
                    self.rwyInformation[0].append(curRwy)
            
            elif sp[0:3] == 'DEP':
                # DEP.
                dep = strSplit[1].replace('DEP RWY ','').strip().split(' ')
                self.rwyInformation[1] = []
                for rwy in dep:
                    curRwy = [rwy[0:2],None,None,None]
                    if 'L' in rwy:
                        curRwy[1] = 'Left'
                    if 'C' in rwy:
                        curRwy[2] = 'Center'
                    if 'R' in rwy:
                        curRwy[3] = 'Right'
                    self.rwyInformation[1].append(curRwy)
                    
            elif sp[0:3] == 'TRL':
                self.rwyInformation[2] = sp.strip().replace('TRL FL','')
                
            elif sp[0:2] == 'TA':
                self.rwyInformation[3] = sp.strip().replace('TA ','').replace('FT','')

    
    # Generate a string of the metar for voice generation.
    def parseVoiceMetar(self):
        self.metarVoice = 'Met report'
        #TODO: Test with many possible METARs
        
        # Wind
        if self.metar.wind_speed._value != 0:
            if self.metar.wind_dir is not None:
                self.metarVoice = ('{}, wind {}, {}').format(self.metarVoice,parseVoiceString(self.metar.wind_dir.string()),parseVoiceString(self.metar.wind_speed.string()))
            else:
                self.metarVoice = ('{}, wind variable, {}').format(self.metarVoice,parseVoiceString(self.metar.wind_speed.string()))
        else:
            self.metarVoice = ('{}, wind calm').format(self.metarVoice,self.metar.wind_dir.string(),self.metar.wind_speed.string())
        
        if self.metar.wind_gust is not None:
            self.metarVoice = ('{}, maximum {}').format(self.metarVoice,parseVoiceString(self.metar.wind_gust.string()))
        
        if self.metar.wind_dir_from is not None:
            self.metarVoice = ('{}, variable between {} and {}').format(self.metarVoice,parseVoiceString(self.metar.wind_dir_from.string()),parseVoiceString(self.metar.wind_dir_to.string()))
            
        
        # Visibility.
        #TODO: implement directions
        self.metarVoice = ('{}, visibility {}').format(self.metarVoice,self.metar.vis.string())
        
        # runway visual range
        if self.metar.runway_visual_range():
            self.metarVoice = ('{}, visual range {}').format(self.metarVoice,self.metar.runway_visual_range().replace(';', ','))
        
        # weather phenomena
        if self.metar.weather:
            self.metarVoice = '{}, {}'.format(self.metarVoice,self.metar.present_weather().replace(';',','))
        
        # clouds
        self.metarVoice = '{}, {}'.format(self.metarVoice,self.metar.sky_conditions(',').replace(',',', ').replace('a few','few'))
        
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
        
    
    # Generate a string of the information identifier for voice generation.
    def parseVoiceInformation(self):
        timeMatch = re.search(r'\d{4}z',self.atisRaw[1])
        startInd = timeMatch.start()
        endInd = timeMatch.end()- 1
        timeStr = parseVoiceInt(self.atisRaw[1][startInd:endInd])
        
        return '{} {} Zulu'.format(self.atisRaw[1][0:startInd-1],timeStr)
    
    
    # Generate a string of the runway information for voice generation.
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
            self.rwyVoice = '{}. '.format(self.rwyVoice[0:-5])
        
        # TRL
        if self.rwyInformation[2] is not None:
            self.rwyVoice = '{}Transition level {}, '.format(self.rwyVoice,parseVoiceInt(self.rwyInformation[2]))
        
        # TA
        if self.rwyInformation[3] is not None:
            self.rwyVoice = '{}Transition altitude {} feet.'.format(self.rwyVoice,self.rwyInformation[3])
            
    
    # Reads the atis string using voice generation.
    def readVoice(self):
        self.engine = pyttsx3.init()
        
        # Set properties currently reading
        self.currentlyReading[0] = self.airport
        self.currentlyReading[1] = self.frequency
        
        # Set properties.
        self.engine.setProperty('voice', self.ENGLISH_VOICE)
        self.engine.setProperty('rate', self.SPEECH_RATE)
        
        # Start listener and loop.
        self.engine.connect('started-word', self.onWord)
        self.engine.say(self.atisVoice)
        self.engine.runAndWait()
    
    
    def onWord(self, name, location, length):  # @UnusedVariable
        self.getPyuipcData()
        
        com1Reading = self.com1frequency == self.currentlyReading[1] and self.com1active
        com2Reading = self.com2frequency == self.currentlyReading[1] and self.com2active
        
        if not com1Reading and not com2Reading:
            self.engine.stop()
            self.currentlyReading = [None,None]
    
    
    ## Reads current frequency and COM2 status.
    def getPyuipcData(self):
        #TODO: Test pyuipc
        if pyuipcImported:
            results = pyuipc.read(self.pyuipcOffsets)
        
            # frequency
            #TODO: Test decode from BCD to float
            hexCode = hex(results[0])[2:]
            self.com1frequency = float('1{}.{}'.format(hexCode[0:2],hexCode[2:]))
            hexCode = hex(results[1])[2:]
            self.com2frequency = float('1{}.{}'.format(hexCode[0:2],hexCode[2:]))
            
            # radio active
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
            self.lat = results[3]
            self.lon = results[4]
        
        else:
            self.com1frequency = self.COM1_FREQUENCY_DEBUG
            self.com2frequency = self.COM2_FREQUENCY_DEBUG
            self.com1active = True
            self.com2active = True
            self.lat = self.LAT_DEBUG
            self.lon = self.LON_DEBUG


    def getAirport(self):
        self.airport = None
        frequencies = []
        if self.com1active:
            frequencies.append(self.com1frequency)
        if self.com2active:
            frequencies.append(self.com2frequency)
            
        if frequencies:
            distanceMin = self.DISTANCE_THRESHOLD + 1
            for ap in self.airportInfos:
                distance = avFormula.gcDistanceNm(self.lat, self.airportInfos[ap][1], self.lon, self.airportInfos[ap][2])
                if self.airportInfos[ap][0] in frequencies and distance < self.DISTANCE_THRESHOLD and distance < distanceMin:
                    distanceMin = distance
                    self.airport = ap
    
    
    def getAirportInfos(self):
        self.airportInfos = {}
        with open(os.path.join(os.path.dirname(self.srcDir),'airports.info')) as aptInfoFile:
            for li in aptInfoFile:
                lineSplit = li.split(',')
                self.airportInfos[lineSplit[0].strip()] = (float(lineSplit[1]),float(lineSplit[2]),float(lineSplit[3]))


if __name__ == '__main__':
    
#     string = 'foo 123 bar 234 foo 1.23 bar 30.04'
#     print(parseVoiceString(string))
    
    voiceAtis = VoiceAtis()
    pass
