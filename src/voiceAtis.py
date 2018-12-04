#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
voiceAtis - Reads an ATIS from IVAO using voice generation
Copyright (C) 2018  Oliver Clemens

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

=========================================================================
CHANGELOG

version 0.0.1 - 03.12.2018
- first version for testing purposes

=========================================================================
ROADMAP

- running version

=========================================================================
"""

import os
import re
from metar.Metar import Metar
import urllib.request
import gzip
# import pyttsx3

## Sperate Numbers with whitespace
# Needed for voice generation to be pronounced properly.
# Example: 250 > 2 5 0
def parseVoiceNumber(number):
        numberSep = ''
        for k in number:
            numberSep = '{}{} '.format(numberSep,k)
        return numberSep.strip()


class VoiceAtis(object):
    
    ENGLISH_VOICE = u'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0'
    GERMAN_VOICE = u'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_DE-DE_HEDDA_11.0'
    STATION_SUFFIXES = ['TWR','APP','GND','DEL','DEP']
    
    ## Setup the VoiceAtis object.
    def __init__(self):
        #TODO: Add FSUIPC code to get ATIS frequency
         
#         self.airport = 'LFMD'
        self.airport = 'EDDM'
#         self.airport = 'LIBR'
#         self.airport = 'LIRF'
#         self.airport = 'EDDS'
        
        # Read whazzup file
#         self.whazzupText = self.getWhazzupText()
        self.whazzupText = self.getWhazzupTextDebug(r'H:\My Documents\Sonstiges\voiceAtis\whazzup_EDDM.txt')
        
        # Parse ATIS.
        if not self.ivac2:
            # Information.
            self.informationVoice = self.parseVoiceInformation(self.atisRaw[1])
            
            # Metar.
            self.metar = Metar(self.atisRaw[2].strip(),strict=False)
            
            # Runways / TRL / TA
            self.rwyInformation = self.parseRawRwy1(self.atisRaw)
            self.rwyVoice = self.parseVoiceRwy(self.rwyInformation)
        
        # Parse voice.
        self.metarVoice = self.parseVoiceMetar()
        
        atisVoice = '{}. {}. {}.'.format(self.informationVoice,self.metarVoice,self.rwyVoice)
        
        
        print(self.atisRaw)
        print(atisVoice)
        
#         self.readVoice()
    
    ## Downloads and reads the whazzup from IVAO 
    def getWhazzupText(self):
        urllib.request.urlretrieve('http://api.ivao.aero/getdata/whazzup/whazzup.txt.gz', 'whazzup.txt.gz')
        with gzip.open('whazzup.txt.gz', 'rb') as f:
            self.whazzupText = f.read().decode('iso-8859-15')
        os.remove('whazzup.txt.gz')
    
    ## Reads a whazzup file on disk.
    # For debug purposes.
    def getWhazzupTextDebug(self,whazzupPath):
        with open(whazzupPath) as whazzupFile:
            self.whazzupText = whazzupFile.read()
    
    ## Find a station of the airport and read the ATIS string.
    def parseWhazzupText(self):
        # Find an open station
        for st in self.STATION_SUFFIXES:
            matchObj = re.search('{}\w*?_{}'.format(self.station,st),self.whazzupText)
            
            if matchObj is not None:
                break
        
        if matchObj is None:
            raise(Exception,'No station found')
        
        # Extract ATIS.
        lineStart = matchObj.start()
        lineEnd = self.whazzupText.find('\n',matchObj.start())
        stationInfo = self.whazzupText[lineStart:lineEnd].split(':')
        self.ivac2 = bool(int(stationInfo[39][0]) - 1)
        self.atisRaw = stationInfo[35].split('^§')
    
    ## Parse runway and transition data.
    # Get active runways for arrival and departure.
    # Get transistion level and altitude.
    def parseRawRwy1(self,atisRaw):
        strSplit = atisRaw[3].split(' / ')
        
        # ARR.
        arr = strSplit[0].replace('ARR RWY ','').strip().split(' ')
        arrRwys = []
        for rwy in arr:
            curRwy = [rwy[0:2],None,None,None]
            if 'L' in rwy:
                curRwy[1] = 'Left'
            if 'C' in rwy:
                curRwy[2] = 'Center'
            if 'R' in rwy:
                curRwy[3] = 'Right'
            arrRwys.append(curRwy)
            
        # DEP.
        dep = strSplit[1].replace('DEP RWY ','').strip().split(' ')
        depRwys = []
        for rwy in dep:
            curRwy = [rwy[0:2],None,None,None]
            if 'L' in rwy:
                curRwy[1] = 'Left'
            if 'C' in rwy:
                curRwy[2] = 'Center'
            if 'R' in rwy:
                curRwy[3] = 'Right'
            depRwys.append(curRwy)
            
        # TRL
        trl = strSplit[2].strip().replace('TRL FL','')
        
        # TA
        ta = strSplit[3].strip().replace('TA ','').replace('FT','')
        
        return [arrRwys,depRwys,trl,ta]
    
    # Generate a string of the metar for voice generation.
    def parseVoiceMetar(self):
        metarVoice = 'Met report'
        
        
        # Wind
        windDirStr = '{:03d}'.format(int(self.metar.wind_dir._degrees))
        
        windSpeed = parseVoiceNumber(str(int(self.metar.wind_speed._value)))
        
        if int(self.metar.wind_speed._value) != 1:
            metarVoice = ('{}, wind {} {} {} degrees, {} knots').format(metarVoice,windDirStr[0],windDirStr[1],windDirStr[2],windSpeed)
        else:
            metarVoice = ('{}, wind {} {} {} degrees, {} knot').format(metarVoice,windDirStr[0],windDirStr[1],windDirStr[2],windSpeed)
        
        # Visibility.
        
        return metarVoice
    
    # Generate a string of the information identifier for voice generation.
    def parseVoiceInformation(self,atisRaw):
        timeMatch = re.search(r'\d{4}z',atisRaw)
        startInd = timeMatch.start()
        endInd = timeMatch.end()- 1
        timeStr = parseVoiceNumber(atisRaw[startInd:endInd])
        
        return '{} {} Zulu'.format(atisRaw[0:startInd-1],timeStr)
    
    # Generate a string of the runway information for voice generation.
    def parseVoiceRwy(self,rwyInformation):
        rwyVoice = ''
        
        # ARR.
        rwyVoice = '{}Arrival runway '.format(rwyVoice)
        for arr in rwyInformation[0]:
            if arr[1:4].count(None) == 3:
                rwyVoice = '{}{} and '.format(rwyVoice,parseVoiceNumber(arr[0]))
            else:
                for si in arr[1:4]:
                    if si is not None:
                        rwyVoice = '{}{} {} and '.format(rwyVoice,parseVoiceNumber(arr[0]),si)
        rwyVoice = rwyVoice[0:-5]
        
        # DEP.
        rwyVoice = '{} Departure runway '.format(rwyVoice)
        for dep in rwyInformation[0]:
            if dep[1:4].count(None) == 3:
                rwyVoice = '{}{} and '.format(rwyVoice,parseVoiceNumber(dep[0]))
            else:
                for si in dep[1:4]:
                    if si is not None:
                        rwyVoice = '{}{} {} and '.format(rwyVoice,parseVoiceNumber(dep[0]),si)
        rwyVoice = rwyVoice[0:-5]
        
        return rwyVoice
    
    # Reads the atis string using voice generation.
    def readVoice(self):
        engine = pyttsx3.init()
        
        # Set properties.
        engine.setProperty('voice', self.ENGLISH_VOICE)
        print(engine.getProperty('rate'))
        engine.setProperty('rate', 140)
        
        # Start listener and loop.
        engine.connect('started-word', self.onWord)
        engine.say(self.atisVoice)
        engine.runAndWait()
    
    def onWord(self):
        pass
        

if __name__ == '__main__':
    voiceAtis = VoiceAtis()
    pass
