from __future__ import division

import os
import re


XP_FOLDER = r"C:\X_Plane 11"

apFilePath = os.path.join(XP_FOLDER,r"Resources\default scenery\default apt dat\Earth nav data\apt.dat")



apCount = 0
# airports = {}

curAirportCode = None
curAirportName = None
curAtis = None
curLat = None
curLon = None

with open(apFilePath) as apFile:
    with open('apData.txt','w') as apDataFile:
        for lineid,line in enumerate(apFile):
            line = line.replace('\n','')
            lineSplit = re.split('  *',line)
    #         # Get airport code
            if lineSplit[0] == '1':
#                 apCount += 1
                # Store last airport
                if curAirportCode is not None and curAtis is not None:
                    apCount += 1
                    if curLat is None:
                        curLat = 0.0
                    if curLon is None:
                        curLon = 0.0
                    
                    
                    apDataFile.write('{} {:6.2f} {:11.6f} {:11.6f} {}\n'.format(curAirportCode,curAtis,curLat,curLon,curAirportName))
#                     airports[curAirportCode] = [curAiportName,curAtis,curLat,curLon]
                    pass
                 
                curAirportCode = lineSplit[4]
                curAirportName = lineSplit[5]
                curAtis = None
                curLat = None
                curLon = None
            elif lineSplit[0] == '50' and lineSplit[2] == 'ATIS':
                # Store ATIS frequency
                curAtis = int(lineSplit[1])/100
                pass
            elif lineSplit[0] == '1302':
                if lineSplit[1] == 'datum_lat':
                    try:
                        curLat = float(lineSplit[2])
                    except ValueError:
                        curLat = 0.0
                elif lineSplit[1] == 'datum_lon':
                    try:
                        curLon = float(lineSplit[2])
                    except ValueError:
                        curLat = 0.0
            
#             apDataFile.write(line)
#             print(line.replace('\n',''))
#             if apCount > 3:
#                 break

            if not (lineid % 100000):
                print('{} lines parsed.'.format(lineid))
                
pass
        
        
        
        