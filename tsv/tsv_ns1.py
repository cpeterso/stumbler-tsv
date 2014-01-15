#!/usr/bin/env python

from __future__ import absolute_import, division

import calendar
import logging
import re
import sys
import time

import wifi


# Latitude	Longitude	( SSID )	Type	( BSSID )	Time (GMT)	[ SNR Sig Noise ]	# ( Name )	Flags	Channelbits	BcnIntvl
# N 43.6477510	W 79.3932570	( aghq2 )	BSS	( 90:27:E4:5E:65:B1 )	05:38:01 (GMT)	[ 12 12 0 ]	# ( Apple )	0011	0000	0

_R = re.compile('([NS]) (\d{1,3}\.\d+)\t([EW]) (\d{1,3}\.\d+)\t\( (.+) \)\t(ad-hoc|I?BSS|\?\?\?)\t\( ((?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}) \)\t(\d\d:\d\d:\d\d \(GMT\))\t\[ +(\d+) +(?:\d+ \d+ )?\]\t#')

wifi.test_re(_R, 9, [
    'N 43.6477510	W 79.3932570	( aghq2 )	BSS	( 90:27:E4:5E:65:B1 )	05:38:01 (GMT)	[ 12 12 0 ]	# ( Apple )	0011	0000	0',
    'N 43.6477510	W 79.3932570	( hhonors )	BSS	( 00:23:5D:8D:40:F0 )	05:38:01 (GMT)	[ 37 37 0 ]	# ( Cisco Systems )	0001	0000	0',
    'N 43.6465990	W 79.3943710	( HP8C116C )	IBSS	( 02:2A:2A:6E:AF:6B )	05:36:28 (GMT)	[ 4 4 0 ]	# ( unknown )	0002	0000	0',
    'N 50.8414667	E 4.3660500	( bombolong )	ad-hoc	( 02:02:cf:87:27:b5 )	01:00:00 (GMT)	[  76  ]	# ( NULL )	0002	0002	',
    ])


def _ns1_parse_line(line):
    if line[0] == '#':
        return None

    m = _R.match(line)
    if m is None:
        logging.error('no match: %s', line)
        assert False

    (ns, latitude, ew, longitude, ssid, bss, bssid, timeofday, snr) = m.groups()

    latitude = float(latitude)
    if ns == 'S':
        latitude *= -1

    longitude = float(longitude)
    if ew == 'W':
        longitude *= -1

    NS1_EPOCH = "2012-04-25"

    # 05:38:01 (GMT)
    st = time.strptime(NS1_EPOCH + ' ' + timeofday, '%Y-%m-%d %H:%M:%S (GMT)')
    timestamp = calendar.timegm(st)

    snr = int(snr)
    wifi.check("snr", snr, 0 <= snr <= 99)
    dbm = -99 + snr # HACK

    bssid = wifi.canonicalize_bssid(bssid)

    return wifi.AP(timestamp=timestamp,
                   bssid=bssid,
                   latitude=latitude,
                   longitude=longitude,
                   signal=dbm,
                   ssid=ssid)


for filename in sys.argv[1:]:
    with open(filename, 'r') as file:
        wifi.print_as_tsv(file, _ns1_parse_line)
