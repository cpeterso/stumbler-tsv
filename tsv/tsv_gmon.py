#!/usr/bin/env python

from __future__ import absolute_import, division

import calendar
import logging
import re
import sys
import time

import wifi

# BSSID;LAT;LON;SSID;Crypt;Beacon Interval;Connection Mode;Channel;RXL;Date;Time

_R = re.compile(r"""((?:[0-9A-F]{2}:){5}[0-9A-F]{2});           # BSSID
                    ((?:NaN|(?:-?\?)|(?:-?\d{1,2}(?:\.\d+)?))); # Latitude
                    ((?:NaN|(?:-?\?)|(?:-?\d{1,3}(?:\.\d+)?))); # Longitude
                    (.{0,32});                                  # SSID
                    (?:Open|Wep|WPA2|WpaPsk|\?);                # Security
                    (?:-\d{2,4});                               # Beacon Interval
                    (?:Infra|Open);                             # Connection Mode
                    ([1-9]\d{0,2});                             # Channel
                    (-\d{1,3});                                 # RXL
                    ((?:19|20)?\d{2}/[0-2]\d/[0-3]\d);          # Date
                    ([0-2]\d:[0-5]\d:[0-5]\d)                   # Time
                    """, re.X)

wifi.test_re(_R, 8, [
    "00:00:C5:B2:18:7C;46.80945;7.14751;johannes;Wep;-81;Infra;7;-79;2013/12/04;18:00:33",
    "FE:F5:28:D1:37:80;46.50299;6.48682;Passion-Cuisine;WpaPsk;-71;Infra;6;-66;2013/12/22;21:37:06",
    "FE:F5:28:D1:38:70;46.52202;6.62910;kolal;WPA2;-90;Infra;13;-88;2014/01/01;04:05:53",
    "00:14:A9:74:FA:40;46.20082;6.14352;((o)) ville-geneve;Open;-70;Infra;6;-68;2014/01/04;15:12:53",
    "00:01:E3:A8:1B:A8;46.18885;6.09936;ConnectionPoint;?;-88;Infra;6;-86;2014/01/12;16:39:58",
    "00:02:6F:5F:EA:76;NaN;NaN;bnet;WpaPsk;-5089;Infra;4;-90;2012/09/23;20:15:00",
    ])


_lineno = 0

def _gmon_csv_parse_line(line):
    global _lineno
    _lineno += 1
    if _lineno == 1:
        assert re.match("BSSID;LAT;LON;SSID;Crypt;Beacon Interval;Connection Mode;Channel;RXL;Date;Time", line)
        return None

    m = _R.match(line)
    if m is None:
        print logging.error('no match: %s', line)
        assert False

    (bssid, latitude, longitude, ssid, channel, signal, date_, time_) = m.groups()

    if latitude == "NaN" or longitude == "NaN":
        return None

    bssid = wifi.canonicalize_bssid(bssid)
    latitude = float(latitude)
    longitude = float(longitude)
    channel = int(channel)
    signal = int(signal)

    datetime = date_ + time_
    st = time.strptime(datetime, '%Y/%m/%d%H:%M:%S')
    timestamp = calendar.timegm(st)

    return wifi.AP(timestamp=timestamp,
                   bssid=bssid,
                   latitude=latitude,
                   longitude=longitude,
                   channel=channel,
                   signal=signal,
                   ssid=ssid)


for filename in sys.argv[1:]:
    with open(filename, 'r') as file:
        _lineno = 0
        wifi.print_as_tsv(file, _gmon_csv_parse_line)
