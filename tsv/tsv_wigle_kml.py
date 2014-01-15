#!/usr/bin/env python

from __future__ import absolute_import, division

from xml.etree import ElementTree

import calendar
import logging
import re
import string
import sys
import time

from record import Record

import wifi


_WIGLE_PLACEMARK_TAG = '{http://www.opengis.net/kml/2.2}Placemark'
_NAME_TAG = '{http://www.opengis.net/kml/2.2}name'
_DESCRIPTION_TAG = '{http://www.opengis.net/kml/2.2}description'
_COORDINATES_TAG ='{http://www.opengis.net/kml/2.2}Point/{http://www.opengis.net/kml/2.2}coordinates'


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
    description = description.split('<br/>')
    for kv in description:
        key, value = kv.split(': ', 1)
        d[key] = value[3:-4]

    bssid = d['BSSID']
    # FIXME: Parse BSSIDs like "31040410_56978_2731527"
    if re.match("\d+_\d{5}_\d+", bssid):
        bssid = wifi.NULL_BSSID
    bssid = wifi.canonicalize_bssid(bssid)

    channel = 0
    signal = 0
    timestamp = int(d['Timestamp']) // 1000

    return wifi.Record(bssid=bssid,
                       channel=channel,
                       signal=signal,
                       timestamp=timestamp)


def _parse_coordinates(coordinates):
    coordinates = coordinates.split(',')
    longitude = float(coordinates[0])
    latitude = float(coordinates[1])
    return Record(latitude=latitude, longitude=longitude)


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
                   channel=desc.channel,
                   signal=desc.signal,
                   ssid=ssid)

def _print_kml_as_tsv(filename):
    etree = ElementTree.iterparse(filename)
    for event, element in etree:
        if element.tag == _WIGLE_PLACEMARK_TAG:
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


for filename in sys.argv[1:]:
    _print_kml_as_tsv(filename)
