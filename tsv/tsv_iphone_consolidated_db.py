#!/usr/bin/env python

from __future__ import absolute_import, division

import calendar
import logging
import re
import sys
import time

import wifi


_R = re.compile('"((?:[0-9a-f]{1,2}:){5}[0-9a-f]{1,2})","(\d{9,}\.\d+)","(0|-?\d{1,2}\.\d+)","(0|-?1?\d{1,2}\.\d+)","(-1|\d{2,3})","0","-1","-1","-1","(0|50|60|65|68|70)"')

wifi.test_re(_R, 6, [
    '"0:26:50:8c:a:31","298883375.530953","37.84438252","-122.25573939","82","0","-1","-1","-1","50"',
    '"0:18:3f:f1:68:9","298883372.481177","37.84098821","-122.2467215","70","0","-1","-1","-1","50"',
    '"0:22:57:98:b9:82","299216214.392777","37.88997","-122.13794016","60","0","-1","-1","-1","50"',
    '"0:b:33:2:0:c","299278325.481233","0","0","-1","0","-1","-1","-1","0"',
    ])


# http://nelsonslog.wordpress.com/2011/04/22/iphone-consolidated-db-location-tracking-notes/
# Timestamps are like 309803342: I believe this is NSDate seconds since 1 Jan 2001. Add 978307200 to get it in seconds since Unix 1970 epoch.
def _timestamp_from_nsdate(nsdate):
    return int(nsdate + 978307200.5)


def _iphone_consolidated_db_parse_line(line):
    m = _R.match(line)
    if m is None:
        print logging.error('no match: %s', line)
        assert False

    (bssid, nsdate, latitude, longitude, signal, confidence) = m.groups()

    bssid = wifi.canonicalize_bssid(bssid)
    timestamp = _timestamp_from_nsdate(float(nsdate))
    latitude = float(latitude)
    longitude = float(longitude)
    signal = -int(signal)

    confidence = int(confidence)
    wifi.check('confidence', confidence, confidence in [0, 50, 60, 65, 68, 70])

    return wifi.AP(timestamp=timestamp,
                   bssid=bssid,
                   latitude=latitude,
                   longitude=longitude)


for filename in sys.argv[1:]:
    with open(filename, 'r') as file:
        wifi.print_as_tsv(file, _iphone_consolidated_db_parse_line)
