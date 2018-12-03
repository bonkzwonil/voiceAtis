#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
'''
Created on 03.12.2018

@author: clemeno
'''

import os
import re
from metar.Metar import Metar
import urllib.request
import gzip
import pyttsx3




def getWhazzupText():
    urllib.request.urlretrieve('http://api.ivao.aero/getdata/whazzup/whazzup.txt.gz', 'whazzup.txt.gz')
    with gzip.open('whazzup.txt.gz', 'rb') as f:
        whazzupText = f.read().decode('iso-8859-15')
    os.remove('whazzup.txt.gz')
    
    return whazzupText

def parseRawRwy1(atisRaw):
    strSplit = atisRaw[3].split(' / ')
    #'ARR RWY 26L/R / DEP RWY 26L/R / TRL FL70 / TA 5000FT'
    
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

def parseVoiceNumber(number):
    numberSep = ''
    for k in number:
        numberSep = '{}{} '.format(numberSep,k)
    return numberSep.strip()


def parseVoiceMetar(metar):
    metarVoice = 'Met report'
    
    
    # Wind
    windDirStr = '{:03d}'.format(int(metar.wind_dir._degrees))
    
    windSpeed = parseVoiceNumber(str(int(metar.wind_speed._value)))
    
    if int(metar.wind_speed._value) != 1:
        metarVoice = ('{}, wind {} {} {} degrees, {} knots').format(metarVoice,windDirStr[0],windDirStr[1],windDirStr[2],windSpeed)
    else:
        metarVoice = ('{}, wind {} {} {} degrees, {} knot').format(metarVoice,windDirStr[0],windDirStr[1],windDirStr[2],windSpeed)
    
    # Visibility.
    
    return metarVoice


def parseVoiceInformation(atisRaw):
    timeMatch = re.search(r'\d{4}z',atisRaw)
    startInd = timeMatch.start()
    endInd = timeMatch.end()- 1
    timeStr = parseVoiceNumber(atisRaw[startInd:endInd])
    
    return '{} {} Zulu'.format(atisRaw[0:startInd-1],timeStr)
    
def parseVoiceRwy(rwyInformation):
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
    
    
# def parseVoiceRwy(atisRaw):
#     pass

if __name__ == '__main__':
    # Constants.
    ENGLISH_VOICE = u'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0'
#     ENGLISH_VOICE = u'\\HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_DE-DE_HEDDA_11.0'
    STATION_SUFFIXES = ['TWR','APP','GND','DEL','DEP']

    #TODO: Get whazzup file automatically
    
    
    #TODO: Add FSUIPC code to get ATIS frequency
     
    # station = 'LFMD'
    station = 'EDDM'
    # station = 'LIBR'
    # station = 'LIRF'
#     station = 'EDDS'
    
    # # Read whazzup file
    # with open(os.path.join(os.path.dirname(os.getcwd()),'whazzup_EDDM.txt')) as whazzupFile:
    #     whazzupText = whazzupFile.read()
    
    whazzupText = getWhazzupText()
    
    # Find an open station
    for st in STATION_SUFFIXES:
        matchObj = re.search('{}\w*?_{}'.format(station,st),whazzupText)
        
        if matchObj is not None:
            break
    
    if matchObj is None:
        raise(Exception,'No station found')
    
    # Extract ATIS.
    lineStart = matchObj.start()
    lineEnd = whazzupText.find('\n',matchObj.start())
    stationInfo = whazzupText[lineStart:lineEnd].split(':')
    ivac2 = bool(int(stationInfo[39][0]) - 1)
    atisRaw = stationInfo[35].split('^§')
    
    # # Parse ATIS.
    if not ivac2:
        # Information.
        informationVoice = parseVoiceInformation(atisRaw[1])
        
        # Metar.
        metar = Metar(atisRaw[2].strip(),strict=False)
        
        # Runways / TRL / TA
        rwyInformation = parseRawRwy1(atisRaw)
        rwyVoice = parseVoiceRwy(rwyInformation)
        
        
        
    
    # Parse voice.
    # informationVoice = 
    metarVoice = parseVoiceMetar(metar)
    
    atisVoice = '{}. {}. {}.'.format(informationVoice,metarVoice,rwyVoice)
    
    
    print(atisRaw)
    print(atisVoice)
    
    engine = pyttsx3.init()
    engine.setProperty('voice', ENGLISH_VOICE)
    print(engine.getProperty('rate'))
    engine.setProperty('rate', 140)
    
    
    engine.say(atisVoice)
    engine.runAndWait()
     
     
    # obs = Metar('EDDS 030920Z 22007KT 170V260 9999 VCSH FEW010 SCT035TCU 13/11 Q1008 NOSIG')
    
    
    
    
    
    pass
