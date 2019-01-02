#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#==============================================================================
# voiceAtisGUI - A GUI to show information from and control voiceAtis
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
from __future__ import __division__

from Tkinter import Tk

from voiceAtis import VoiceAtis

class voiceAtisGUI(object):



    def __init__(self):
        """
        Constructor details here
        """
        self.master = Tk()
        self.master.title('FPLGUI')
        self.master.resizable(0, 0)
        
        self.voiceAtis = VoiceAtis()
        
        
if __name__ == '__main__':
    pass