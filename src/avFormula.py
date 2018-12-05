'''
Created on 26.11.2018

@author: clemeno
'''

from math import sin,asin,cos,acos,tan,sqrt,radians,degrees,pi #@UnusedImport

## Calculates the great circle distance in arc angle.
def gcDistance(lat1,lat2,lon1,lon2):
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    lon1 = radians(lon1)
    lon2 = radians(lon2)
    return 2*asin(sqrt((sin((lat1-lat2)/2))**2 + cos(lat1)*cos(lat2)*(sin((lon1-lon2)/2))**2));

def gcDistanceNm(lat1,lat2,lon1,lon2):
    return ((180*60)/pi)*gcDistance(lat1,lat2,lon1,lon2)