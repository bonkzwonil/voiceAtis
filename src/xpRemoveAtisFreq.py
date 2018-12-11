#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#==============================================================================
# xpRemoveAtisFreq - Removes Atis Freq from XP to disable standard atis
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

import os
from shutil import copyfile

XP_FOLDER = r"H:\My Documents\Sonstiges\XP11"

aptDatFolder = os.path.join(XP_FOLDER,r"Resources\default scenery\default apt dat\Earth nav data")

if not os.path.isfile(os.path.join(aptDatFolder,'apt.dat.bak')):
    copyfile(os.path.join(aptDatFolder,'apt.dat'), os.path.join(aptDatFolder,'apt.dat.bak'))

with open(os.path.join(aptDatFolder,'apt.dat.bak')) as aptOldFile:
    with open(os.path.join(aptDatFolder,'apt.dat'),'w') as aptNewFile:
        for lineid, line in aptOldFile:
            if not line.startswith('50'):
                aptNewFile.write(line)
            
            if not (lineid % 100000):
                print('{} lines parsed.'.format(lineid))