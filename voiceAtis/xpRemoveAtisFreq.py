#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#==============================================================================
# xpRemoveAtisFreq - Removes Atis Freq from XP to disable standard atis
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

import os
import sys
from io import open
from time import sleep
from shutil import copyfile
from Tkinter import Tk
from tkFileDialog import askdirectory
from tkMessageBox import askyesno

# Create root window for askdirectory and askyesno.
root = Tk()
root.withdraw()

# Get X-Plane directory.
xpFolder = askdirectory(initialdir = 'C:\\' ,title = 'Select X-Plane directory')

# Ask for confirmation
doIt = askyesno("Caution","This will remove all ATIS frequency from X-Plane!\nProceed (at own risk)?\nA backup will be provided.")
root.destroy()

# Abort if no confirmation.
if not doIt:
    sys.exit("Aborted by user.")

# Get folder.
aptDatFolder = os.path.join(xpFolder,r"Resources\default scenery\default apt dat\Earth nav data")
if not os.path.isfile(os.path.join(aptDatFolder,'apt.dat')):
    sys.exit("apt.dat not found.\nMake sure that you choose the right path and that the file structure is correct.")

# Create backup
if not os.path.isfile(os.path.join(aptDatFolder,'apt.dat.bak')):
    copyfile(os.path.join(aptDatFolder,'apt.dat'), os.path.join(aptDatFolder,'apt.dat.bak'))
    print('Backup created: {}'.format(os.path.join(aptDatFolder,'apt.dat.bak')))
else:
    print('Backup already present: {}'.format(os.path.join(aptDatFolder,'apt.dat.bak')))

# Get file size and init byteCount.
fileSize = os.path.getsize(os.path.join(aptDatFolder,'apt.dat.bak'))
byteCount = 0
lastPrint = 0

# Process file
print('Starting file processing. This may take some time.')
sys.stdout.write("Progress: {:3}%\r".format(0))
sys.stdout.flush()
try:
    with open(os.path.join(aptDatFolder,'apt.dat.bak'), encoding="utf8") as aptOldFile:
        with open(os.path.join(aptDatFolder,'apt.dat'),'w',newline='\n', encoding="utf8") as aptNewFile:
            for lineid, line in enumerate(aptOldFile):
                
                # Delete all lines starting with "50"
                if not line.startswith('50'):
                    aptNewFile.write(line)
                
                # Get read bytes
                byteCount += len(line)
                progress = (byteCount * 100) / fileSize 
                
                # Print if 1% step.
                if progress > lastPrint:
                    lastPrint = progress
                    sys.stdout.write("\rProgress: {:3}%".format(progress))
                    sys.stdout.flush()
except:
    print('Error processing file: {}'.format(sys.exc_info()[0]))
    copyfile(os.path.join(aptDatFolder,'apt.dat.bak'), os.path.join(aptDatFolder,'apt.dat'))
    sys.exit('Aborted and restored backup.')
else:
    sys.stdout.write("\rProgress: 100%")
    sys.stdout.flush()
    print('\nFinished!')
    sleep(10)