#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#==============================================================================
# avFormula - Some usefull formula in globe and aviation context
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
# Inspired by Aviation Formulary V1.46 by Ed Williams.
# -> http://www.edwilliams.org/avform.htm
#==============================================================================

from math import sin,asin,cos,acos,tan,atan2,sqrt,radians,degrees,pi #@UnusedImport

## Calculates the great circle distance in arc angle.
def gcDistance(lat1,lat2,lon1,lon2):
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    lon1 = radians(lon1)
    lon2 = radians(lon2)
    return 2*asin(sqrt((sin((lat1-lat2)/2))**2 + cos(lat1)*cos(lat2)*(sin((lon1-lon2)/2))**2));

## Calculates the great circle distance in nautical miles.
def gcDistanceNm(lat1,lat2,lon1,lon2):
    return ((180*60)/pi)*gcDistance(lat1,lat2,lon1,lon2)

## Calculates the intermediate coordinates of two points on earth.
def gcIntermediatePoint(lat1,lat2,lon1,lon2,*args):
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    lon1 = radians(lon1)
    lon2 = radians(lon2)
    
    # If args not given, calc middle intermediate point.
    if len(args):
        f = args[0]
    else:
        f = 0.5
    
    # Calc gc distance between points.
    d = gcDistance(lat1,lat2,lon1,lon2)

    # Calc intermediate point.
    A=sin((1-f)*d)/sin(d)
    B=sin(f*d)/sin(d)
    x = A*cos(lat1)*cos(lon1) +  B*cos(lat2)*cos(lon2)
    y = A*cos(lat1)*sin(lon1) +  B*cos(lat2)*sin(lon2)
    z = A*sin(lat1)           +  B*sin(lat2)
    lat=atan2(z,sqrt(x**2+y**2))
    lon=atan2(y,x)
    
    return [degrees(lat),degrees(lon)]