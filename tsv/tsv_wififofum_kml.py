#!/usr/bin/env python

from __future__ import absolute_import, division

from xml.etree import ElementTree

import calendar
import logging
import string
import sys
import time

from record import Record

import wifi

_PLACEMARK_TAG = '{http://earth.google.com/kml/2.2}Placemark'
_NAME_TAG = '{http://earth.google.com/kml/2.2}name'
_DESCRIPTION_TAG = '{http://earth.google.com/kml/2.2}description'
_COORDINATES_TAG ='{http://earth.google.com/kml/2.2}Point/{http://earth.google.com/kml/2.2}coordinates'


def _parse_ssid(ssid):
    ssid = ssid.encode('utf_8')
    MAX_SSID_LENGTH = 32
    if len(ssid) > MAX_SSID_LENGTH:
        raise ValueError('Bad SSID "%s"' % ssid)
    if ssid == '(null)':
        ssid = ''
    return ssid


def _parse_description(description):
    d = {}
    description = description.split('<br>')
    for kv in description:
        key, value = kv.split(': ', 1)
        d[key] = value

    bssid = wifi.canonicalize_bssid(d['MAC'])
    channel = int(d['Channel'])
    signal = int(d['MaxRssi'])

    security = d['Security']
    if security not in ['None', 'Open', 'WEP', 'WPA', 'WPA2']:
        raise ValueError('Bad security "%s"' % security)

    # LastSeen: 'YYYY-MM-DD HH:MM:SS +0000'
    KML_DATETIME_FORMAT_0000 = '%Y-%m-%d %H:%M:%S +0000'
    KML_DATETIME_FORMAT_0700 = '%Y-%m-%d %H:%M:%S -0700'
    KML_DATETIME_FORMAT_0800 = '%Y-%m-%d %H:%M:%S -0800'
    last_seen = d['LastSeen']
    try:
        st = time.strptime(last_seen, KML_DATETIME_FORMAT_0000)
    except:
        try :
            st = time.strptime(last_seen, KML_DATETIME_FORMAT_0700)
        except:
            st = time.strptime(last_seen, KML_DATETIME_FORMAT_0800)
    timestamp = calendar.timegm(st)

    return Record(bssid=bssid,
                  channel=channel,
                  signal=signal,
                  timestamp=timestamp)


def _parse_coordinates(coordinates):
    coordinates = coordinates.split(',')
    longitude = float(coordinates[0])
    latitude = float(coordinates[1])
    altitude = float(coordinates[2])
    wifi.check('altitude', altitude, wifi.MIN_ALTITUDE <= altitude <= wifi.MAX_ALTITUDE)
    return Record(latitude=latitude,
                  longitude=longitude,
                  altitude=altitude)


def _parse_placemark(placemark):
    def get(tagName):
        return placemark.find(tagName).text
    ssid = _parse_ssid(get(_NAME_TAG))
    desc = _parse_description(get(_DESCRIPTION_TAG))
    coordinates = _parse_coordinates(get(_COORDINATES_TAG))

    return wifi.AP(timestamp=desc.timestamp,
                   bssid=desc.bssid,
                   latitude=coordinates.latitude,
                   longitude=coordinates.longitude,
                   altitude=coordinates.altitude,
                   channel=desc.channel,
                   signal=desc.signal,
                   ssid=ssid)


def _print_kml_as_tsv(filename):
    etree = ElementTree.iterparse(filename)
    for event, element in etree:
        if element.tag == _PLACEMARK_TAG:
            try:
                ap = _parse_placemark(element)
                if ap is not None:
                    wifi.print_ap(ap)
            except:
                error = sys.exc_info()[1]
                def get(tagName):
                    return element.find(tagName).text
                logging.warning(_parse_ssid(get(_NAME_TAG)))
                logging.error(error)
                assert False


print '# Timestamp\tBSSID\tLatitude\tLongitude\tSignal\tChannel\tSSID'
for filename in sys.argv[1:]:
    _print_kml_as_tsv(filename)


"""
<kml xmlns="http://earth.google.com/kml/2.2">
<wfff kmlVersion="2.0.1"/>
<Document>
<Placemark>
<name><![CDATA[Evm Basin]]></name>
<description><![CDATA[MAC: 0:15:6d:a9:6f:b3<br>Channel: 11<br>MaxRssi: -95<br>Security: WPA<br>Type: Access Point<br>FirstSeen: 2011-04-09 22:41:34 +0000<br>LastSeen: 2011-04-09 22:41:34 +0000]]></description>
<Point>
<coordinates>-122.303577,37.825634,0.188093</coordinates>
</Point>
</Placemark>

raw_signal_measurements:{
	uid:integer,
	source:str,			# kml, ns1, accesspointslive, wigle.net, gwifi.net
	ip:str,				# CONSTRAINT: "0-255.0-255.0-255.0-255" for hostip.info fallback?
						# Blacklist reserved and bogon addresses:
						# https://secure.wikimedia.org/wikipedia/en/wiki/Reserved_IP_addresses
						# https://secure.wikimedia.org/wikipedia/en/wiki/Bogon_filtering

	timestamp:datetime,	# CONSTRAINT: 2001-01-01T00:00Z <= timestamp <= current time
	eui64:str,			# CONSTRAINT: EUI-64 address: CHAR(20) "01:23:45:67:89:AB:CD" or CHAR(12) "002a1a332f63"
	ssid:ByteString,	# CONSTRAINT: len(ssid) <= 32

	channel:integer,	# CONSTRAINT: 1 <= channel <= 14
	security:str,		# CONSTRAINT: None,WEP,WPA,WPA2

	signal_dBm:float,	# CONSTRAINT: -127 to 80 dBm. Typical range: -80 to -10 dBm.
	# rssi_byte:integer,	# CONSTRAINT: 0-255

	latlong:GeoPt,		# CONSTRAINT: +90N - -90S degrees; -180W - +180E degrees
}
"""
