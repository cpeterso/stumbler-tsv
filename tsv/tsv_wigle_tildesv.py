#!/usr/bin/env python

from __future__ import absolute_import, division

import calendar
import logging
import re
import sys
import time

import wifi

# netid~ssid~trilat~trilong~firsttime~channel~qos~flags~wep~lasttime~transid

_R = re.compile(r"""((?:[0-9a-f]{2}:){5}[0-9a-f]{2})~                                               # netid (BSSID)
                    ([^~]*)~                                                                        # SSID
                    (-?\d{1,2}\.\d{8})~                                                             # trilat
                    (-?\d{1,3}\.\d{8})~                                                             # trilong
                    (?:20[01]\d-[0-2]\d-[0-3]\d|0000-00-00|1969-12-31|1970-01-\d{2})\ 00:00:00~     # firsttime
                    (\d+|\ )~                                                                       # channel
                    ([0-7 ])~                                                                       # qos
                    (\d+|\ )~                                                                       # flags
                    [?2NYW]~                                                                        # wep
                   (20[01]\d-[0-2]\d-[0-3]\d\ 00:00:00)~                                            # lasttime
                    (?:20[01]\d[01]\d[0-3]\d)?                                                      # transid
                    """, re.X)

wifi.test_re(_R, 8, [
    '00:06:25:61:04:d0~linksys macHOME~37.78773880~-122.40343475~2002-05-17 00:00:00~6~0~0001~N~2004-05-03 00:00:00~20020605',
    '00:40:96:5a:e7:d0~<no ssid>~37.79486847~-122.39928436~2002-12-28 00:00:00~0~2~ ~?~2004-05-03 00:00:00~20021228',
    '00:09:43:d0:40:00~~37.79016495~-122.40024567~2003-06-30 00:00:00~0~0~ ~?~2004-05-03 00:00:00~20031230',
    '00:02:2d:09:3f:f0~@SG-WIRELESS~37.79180145~-122.40235138~0000-00-00 00:00:00~0~2~17~?~2004-05-03 00:00:00~20030714',
    '00:90:4b:33:9d:00~wireless~37.78568649~-122.38990021~0000-00-00 00:00:00~ ~0~1~Y~2004-05-03 00:00:00~20030705',
    '02:0b:3d:47:1d:f0~MSHOME~37.78458405~-122.39776611~2003-06-10 00:00:00~17408~0~0012~Y~2004-05-03 00:00:00~20030611',
    '00:03:93:e8:a2:55~rubynet~37.78656387~-122.40242004~2003-04-26 00:00:00~1~0~0411~2~2004-05-03 00:00:00~20030426',
    ])


_lineno = 0

def _wigle_tildesv_parse_line(line):
    global _lineno
    _lineno += 1
    if _lineno == 1:
        return None

    m = _R.match(line)
    if m is None:
        print logging.error('no match: %s', line)
        assert False

    (bssid, ssid, latitude, longitude, channel, qos, flags, datetime) = m.groups()

    bssid = wifi.canonicalize_bssid(bssid)
    latitude = float(latitude)
    longitude = float(longitude)

    if channel == ' ':
        channel = 0
    else:
        channel = int(channel)
    wifi.check_channel(channel)

    # qos: quality of service. It's a value of 0-7. Basically a point starts
    # with 0, it gets up to 4 qos points for being seen on more than one day,
    # it gets up to 4 qos points for being seen by more than one user, and it's
    # capped at 7.
    if qos == ' ':
        qos = 0
    else:
        qos = int(qos)
    assert qos >= 0 and qos <= 7
    signal = -99 + qos * 5 # XXX [-99,-64] dBm

    if flags == ' ':
        flags = 0
    else:
        flags = int(flags)

    # 2011-12-11 00:00:00
    st = time.strptime(datetime, '%Y-%m-%d %H:%M:%S')
    timestamp = calendar.timegm(st)

    if ssid == '<no ssid>' or ssid == '(null)':
        ssid = ''

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
        wifi.print_as_tsv(file, _wigle_tildesv_parse_line)
