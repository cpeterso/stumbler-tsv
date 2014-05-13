#!/usr/bin/env python

from __future__ import absolute_import, division

import calendar
import logging
import re
import sys
import time

import wifi


# BSSID,SSID,AuthMode,Timestamp,Channel,RSSI,Latitude,Longitude,AltitudeMeters,AccuracyMeters[,Type]

_R = re.compile(r"""((?:[0-9a-f]{2}:){5}[0-9a-f]{2}),                            # BSSID
                    (.{0,32}),                                                   # SSID
                    (?:\[.+\])*,                                                 # [Security]
                    ((?:19|20)?\d{2}-[0-2]\d-[0-3]\d\ [0-2]\d:[0-5]\d:[0-5]\d),  # Timestamp
                    ([1-9]\d{0,3}),                                              # Channel
                    (0|(?:-\d{1,3})),                                            # RSSI
                    ((?:-?\?)|(?:-?\d{1,4}(?:\.\d+)?)),                          # Latitude
                    ((?:-?\?)|(?:-?\d{1,4}(?:\.\d+)?)),                          # Longitude
                    (-?\d+(?:\.\d+)?),                                           # Altitude
                    (\d+(?:\.\d+)?)                                              # Accuracy
                    (?:,WIFI)?                                                   # Type
                    """, re.X)

wifi.test_re(_R, 9, [
    "00:22:6b:50:eb:05,dogtown,[WPA2-PSK-CCMP][WPS][ESS],2011-12-11 19:34:21,6,-34,37.8428930835798,-122.247731778771,46,10,WIFI",
    "00:21:7c:36:ea:a1,2WIRE493,[WPA-PSK-TKIP+CCMP][WPA2-PSK-TKIP+CCMP][ESS],2011-12-11 19:34:25,2,-84,37.8429072489962,-122.247739993036,44.2000122070312,15,WIFI",
    "d8:c7:c8:eb:0b:fa,Mozilla Mobile,[WPA2-PSK-CCMP][ESS],2011-12-12 14:25:11,157,-66,37.7896163,-122.3888664,0,38,WIFI",
    "00:24:6c:b8:a3:a2,WL-GW,[WPA2-PSK-CCMP][ESS],1969-12-31 16:00:00,4,-88,37.7877620421609,-122.383854277004,0,35.6734085083008,WIFI",
    "00:1d:e5:8c:aa:30,ResidenceInn_GUEST,[ESS],2012-05-19 10:01:07,8,-74,37.962946370244,-122.053834637627,-20.2999877929688,15,WIFI",
    "74:91:1a:26:e2:b8,St Martins Lane,[ESS],2013-03-06 10:15:21,1,0,51.5112666,-0.127997,0,500,WIFI",
    "00:16:b6:18:44:1f,TheGate 2 (open),[ESS],2013-03-06 13:25:44,11,-3,51.5090621,-0.19607366,86.5999984741211,10,WIFI",
    "44:a7:cf:30:b5:0a,L&B ON THE GO,[WPA-PSK-TKIP][ESS],1969-12-31 16:00:00,1,-65,?,-?,0,1452.03161621094,WIFI",
    "00:0f:66:18:e7:b3,Metrix,[WEP],2010-11-02 19:31:06,6,-71,38.9912224,-77.4250565,0,61",
    "00:21:e8:cc:97:68,Sprint MiFi2200 768 Secure,[WPA2-PSK-CCMP],2010-11-02 19:35:40,11,-88,38.9912728,-77.4247608,0,36",
    "04:4f:aa:2e:39:48,HarborLink - BP Wi-Fi,,2010-11-02 19:41:53,6,-100,38.991276,-77.4248229,0,61",
    "c0:c1:c0:35:2b:00,Lola's,[WPA-PSK-TKIP+CCMP][WPA2-PSK-TKIP+CCMP][WPS][ESS],1969-12-31 16:00:00,11,-82,-?,-?,0,879.535034179688,WIFI",
    "c8:7b:5b:c1:dd:04,molecular_biology,[WPA-PSK-TKIP+CCMP],1970-01-01 08:00:00,10,-92,-660.465344160003,-379.070096429989,0,10818.158203125,WIFI",
    "00:1d:71:e3:8a:4e,Guest,[ESS],2013-09-11 19:11:59,5580,-83,48.52605465,9.05918653,380.700012207031,4,WIFI",
    ])


_lineno = 0

def _wigle_csv_parse_line(line):
    global _lineno
    _lineno += 1
    if _lineno < 2:
        return None
    if _lineno < 3:
        assert re.match("MAC,SSID,AuthMode,FirstSeen,Channel,RSSI,CurrentLatitude,CurrentLongitude,AltitudeMeters,AccuracyMeters,Type", line)
        return None

    m = _R.match(line)
    if m is None:
        if (line.startswith(wifi.NULL_BSSID + ',') or
            line.endswith(',CDMA') or
            line.endswith(',GSM')):
            return None # OK
        print logging.error('no match: %s', line)
        assert False

    (bssid, ssid, datetime, channel, signal, latitude, longitude, altitude, accuracy) = m.groups()

    bssid = wifi.canonicalize_bssid(bssid)
    channel = int(channel)
    signal = int(signal)
    latitude = float(latitude) if latitude != '?' and latitude != '-?' else 0
    longitude = float(longitude) if longitude != '?' and longitude != '-?' else 0
    altitude = float(altitude)
    accuracy = float(accuracy)

    st = time.strptime(datetime, '%Y-%m-%d %H:%M:%S')
    timestamp = calendar.timegm(st)

    wifi.check('altitude', altitude, -130000 <= altitude <= 11000)
    if altitude < wifi.MIN_ALTITUDE or altitude > wifi.MAX_ALTITUDE:
        altitude = 0

    wifi.check('accuracy', accuracy, wifi.MIN_ACCURACY <= accuracy <= 430000)
    if accuracy > wifi.MAX_ACCURACY:
        accuracy = 0

    if latitude < wifi.MIN_LATITUDE or latitude > wifi.MAX_LATITUDE or \
        longitude < wifi.MIN_LONGITUDE or longitude > wifi.MAX_LONGITUDE:
        return None

    return wifi.AP(timestamp=timestamp,
                   bssid=bssid,
                   latitude=latitude,
                   longitude=longitude,
                   accuracy=accuracy,
                   altitude=altitude,
                   channel=channel,
                   signal=signal,
                   ssid=ssid)


for filename in sys.argv[1:]:
    with open(filename, 'r') as file:
        _lineno = 0
        wifi.print_as_tsv(file, _wigle_csv_parse_line)
