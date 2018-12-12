# voiceAtis
Reads an ATIS from IVAO using voice generation

## Requirements
* Python 2.7 - 32 bit (due to pyuipc incompatibility with Python 3 and 64 bit)
* pyuipc
* pyttsx
* XPlane with XPUIPC or MFS, P3D with FSUIPC
* Windows (Linux and Mac not tested yet)

## Installation
* Get the latest version of atisVoice: `git clone https://github.com/Sowintuu/voiceAtis.git`
* Get the latest python 2.7 ([Python releases](https://www.python.org/downloads/))
* Install pyuipc
   * Download [FSUIPC SDK](http://fsuipc.simflight.com/beta/FSUIPC_SDK.zip)
   * Inside this zip-file run `UIPC_SDK_Python.zip\pyuipc-0.3.win32-py2.7.msi`
* Get pyttsx
   * Open a command window in the Python-Script folder
   * Run `pip install pyttsx`

An upload to pypi is on my roadmap.

## Usage
* Start the script "voiceAtis.py"
   * If you would like to see the command output, open it from console. `python voiceAtis.py`
* Start your sim and start a flight.
* Tune the ATIS frequency of the airport where you are parking.
   * Don't forget to activate receive mode of the radio (COM1 or COM2)
* You should hear the ATIS now, if:
   * There is an ATC station online at this airport (TWR, APP, GND or DEL)
   * The airport is in the list of airports with ATIS (airports.info)
   * Feel free to help me by providing frequencies of missing airports!

## Custom airport data
Airport data is downloaded from [ourairports.com](http://ourairports.com). You can see these data at `airports.info` file at main directory. It may happen that this data is inaccurate or an airport is missing.

In this case you can add the airport to the `airports_add.info` file. Airports in this file have priority over downloaded data.

You may inform me about wrong data preferably via the Issues tab. I will then include the data in the airports_add.info to distritbute them to all users. I will also inform [ourairports.com](http://ourairports.com) about the missing or wrong data.

## Bugs and issues
* Please report bugs via the github issues tab.
    * It is usefull to attach the logfile from "root/logs".
    
### Known limitations
* Not able to parse ATIS created by ivac2

## Used packages and Copyright
### python-metar
Used to parse the metar contained in the ATIS.

Copyright (c) 2004-2018, Tom Pollard
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

  Redistributions of source code must retain the above copyright
  notice, this list of conditions and the following disclaimer.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

### pyttsx
Text-to-speech package for python. Used to read the parsed ATIS string.

pyttsx Copyright (c) 2009, 2013 Peter Parente

Permission to use, copy, modify, and distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.


### pyuipc - FSUIPC SDK for Python
Used to get the com frequencies, com status, aircraft coordinates from the simulator.

All Copyright - Peter Dowson and István Váradi.

### [ourairports.com](http://ourairports.com)
OurAirports is a free site where visitors can explore the world's airports, read other people's comments, and leave their own. The help pages have information to get you started.

The site is dedicated to both passengers and pilots. You can create a map of the airports you've visited and share that map with friends. You can find the closest airports to you, and discover the ones that you haven't visited yet.

Behind the fun and features, OurAirports exists primarily as a public good. When Australia forced the US government to shut down public access to its Digital Aeronautical Flight Information File (DAFIF) service in 2006, there was no longer a good source of global aviation data. OurAirports started in 2007 primarily to fill that gap: we encourage members to create and maintain data records for airports around the world, and they manage over 40,000 of them. Many web sites, smartphone apps, and other services rely on OurAirport's data, which is all in the Public Domain (no permission required).

See the [Credits](http://ourairports.com/about.html#credits) for a list of contributers.

## Changelog
### version 0.0.4 - 12.12.2018
* Getting airport data from web now (http://ourairports.com)
    * Option to add additional data

### version 0.0.3 - 07.12.2018
* Now using metar if no ATIS available
* pyuipc tested and running
* Changed RADIO_RANGE to a (realistic) value of 180 nm
* Implemented logging

### version 0.0.2 - 05.12.2018
* Implemented wind gusts and variable wind
* Port to python2 (due to pyuipc)
* Added pyuipc (untested)
* Added logic to get airport

### version 0.0.1 - 03.12.2018
* First version for testing purposes
* Some Atis feartures missing
* No pyuipc
* Voice not tested

## ROADMAP
* Upload to pypi
* Random start
* Get ivac2 atis running
