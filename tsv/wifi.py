from __future__ import absolute_import, division

import logging
import re
import time

from record import Record

NULL_BSSID = "00:00:00:00:00:00"

MIN_ACCURACY, MAX_ACCURACY = 0, 20000       # radius in meters
MIN_ALTITUDE, MAX_ALTITUDE = -418, 8848     # meters, Dead Sea, Mount Everest :)
MIN_LATITUDE, MAX_LATITUDE = -90, +90       # degrees
MIN_LONGITUDE, MAX_LONGITUDE = -180, +180   # degrees
MIN_TIMESTAMP = 946684801                   # 2000-01-01 00:00:01


def check(desc, val, ok):
    if not ok:
        raise ValueError("%s: \"%s\"" % (desc, str(val)))


def check_channel(channel):
    check("channel", channel, 1 <= channel <= 14 or
                              36 <= channel <= 679 or
                              2816 <= channel <= 5580 or
                              16386 <= channel <= 18432 or
                              channel == 0)


# https://en.wikipedia.org/wiki/Received_signal_strength_indication
# Typical wireless signal range is -90 to -10 dBm.
def _dbm_from_rssi(rssi):
    # Vendor    RSSI_Max
    # ======    ========
    # Cisco     100
    # Atheros   60 or 127?
    # Symbol    31
    # My MBP    >= 45?
    check("rssi", rssi, 0 <= rssi <= 100)
    dbm = -99 + rssi # HACK
    check("dbm", dbm, -99 <= dbm <= -10)
    return dbm


_mac_colon_re = re.compile("""([0-9A-Za-z]{1,2}:){5}    # xx:xx:xx:xx:xx:
                               [0-9A-Za-z]{1,2}         # xx """, re.X)

_mac_dash_re = re.compile("""([0-9A-Za-z]{1,2}-){5}     # xx-xx-xx-xx-xx-
                              [0-9A-Za-z]{1,2}          # xx """, re.X)

def canonicalize_bssid(mac):
    def split_mac(separator):
        return tuple([int(xx, 16) for xx in mac.split(separator)])

    if _mac_colon_re.match(mac):
        bytes = split_mac(":")
    elif _mac_dash_re.match(mac):
        bytes = split_mac("-")
    else:
        raise ValueError("Bad BSSID: %s" % mac)

    return "%02x:%02x:%02x:%02x:%02x:%02x" % bytes


_SSID_PREFIX_LIST = [
    "ASUS",
    "AndroidAP",
    "AndroidTether",
    "Galaxy Note",
    "Galaxy S",
    "Galaxy Tab",
    "HTC ",
    "HelloMoto",
    "LG VS910 4G",
    "MIFI",
    "MiFi",
    "Mifi",
    "MOBILE",
    "Mobile",
    "PhoneAP",
    "SAMSUNG",
    "SCH-I",
    "SPRINT",
    "Samsung",
    "Sprint",
    "Verizon",
    "VirginMobile",
    "barnacle", # Android Barnacle Wifi Tether
    "docomo",
    "hellomoto",
    "iPad",
    "iPhone",
    "ipad",
    "mifi",
    "mobile",
    "myLGNet",
    "myTouch 4G Hotspot",
    "samsung",
    "sprint",
    "webOS Network",

    # Transportation Wi-Fi
    "AIRBUS FREE WIFI",
    "AmtrakConnect",
    "GBUS",
    "GBusWifi",
    "SF Shuttle Wireless",
    "SST-PR-1", # Sears Home Service van hotspot?!
    "Shuttle",
    "Trimble ",
    "VTA Free Wi-Fi",
    "ac_transit_wifi_bus",
    "airbusA380",
    "amtrak_",
    "shuttle",
]


_SSID_SUFFIX_LIST = [
    # Mobile devices
    " ASUS",
    "-ASUS",
    "_ASUS",
    "MIFI",
    "MiFi",
    "Mifi",
    "MyWi",
    " Shuttle",
    "Tether",
    "iPad",
    "iPhone",
    "ipad",
    "iphone",
    "mifi",
    "tether",

    # Google's SSID opt-out
    "_nomap",
]

_SSID_SUBSTRING_LIST = [
    "MacBook",
    "MiFi",
    "Mifi",
]

def _is_mobile_ssid(ssid):
    for prefix in _SSID_PREFIX_LIST:
        if ssid.startswith(prefix):
            return True
    for suffix in _SSID_SUFFIX_LIST:
        if ssid.endswith(suffix):
            return True
    for substring in _SSID_SUBSTRING_LIST:
        if ssid.find(substring) != -1:
            return True
    return False

assert _is_mobile_ssid("Steve's iPhone") and _is_mobile_ssid("GBUS Turbo") and not _is_mobile_ssid("not a mobile ssid")


def AP(timestamp, bssid, latitude, longitude, accuracy=None, altitude=None, altitude_accuracy=None, channel=None, signal=None, ssid=""):
    #
    # Fixup measurements
    #
    if timestamp < MIN_TIMESTAMP or timestamp > time.time():
        timestamp = 0

    #
    # Validate measurements
    #
    check("bssid", bssid, bssid == canonicalize_bssid(bssid))
    check("latitude", latitude, MIN_LATITUDE <= latitude <= MAX_LATITUDE)
    check("longitude", longitude, MIN_LONGITUDE <= longitude <= MAX_LONGITUDE)
    check("ssid", ssid, 0 <= len(ssid) <= 32)

    if accuracy:
        check("accuracy", accuracy, MIN_ACCURACY <= accuracy <= MAX_ACCURACY)
    if altitude:
        check("altitude", altitude, MIN_ALTITUDE <= altitude <= MAX_ALTITUDE)
    if altitude_accuracy:
        check("altitude_accuracy", altitude_accuracy, MIN_ACCURACY <= altitude_accuracy <= MAX_ACCURACY)
    if channel:
        check_channel(channel)
    if signal:
        check("signal", signal, -120 <= signal <= 0)

    #
    # Filter out suspicious measurements
    #
    if ((latitude == 0 and longitude == 0) or
        bssid == NULL_BSSID or
        _is_mobile_ssid(ssid)):
        return None

    return Record(timestamp=timestamp,
                  bssid=bssid,
                  latitude=latitude,
                  longitude=longitude,
                  altitude=altitude,
                  accuracy=accuracy,
                  altitude_accuracy=altitude_accuracy,
                  channel=channel,
                  signal=signal,
                  ssid=ssid)


def test_re(r, group_count, tests):
    for test in tests:
        match = r.match(test)
        if match is None:
            logging.error(test)
            assert False
        groups = match.groups()
        if len(groups) != group_count:
            logging.warning(test)
            logging.error(groups)
            assert False


def print_ap(ap):
    print "%s\t%d\t%f\t%f\t%s\t%s\t%s\t%s\t%s\t%s" % (ap.bssid,
                                                      ap.timestamp,
                                                      ap.latitude,
                                                      ap.longitude,
                                                      str(ap.accuracy) if ap.accuracy else "",
                                                      str(ap.altitude) if ap.altitude else "",
                                                      str(ap.altitude_accuracy) if ap.altitude_accuracy else "",
                                                      str(ap.channel) if ap.channel else "",
                                                      str(ap.signal) if ap.signal else "",
                                                      ap.ssid)

"""
BSSID;LAT;LON;SSID;Crypt;Beacon Interval;Connection Mode;Channel;RXL;Date;Time
"0:12:88:a8:28:69","298883372.481177","37.84261929","-122.24882423","89","0","-1","-1","-1","50"
# Latitude	Longitude	( SSID )	Type	( BSSID )	Time (GMT)	[ SNR Sig Noise ]	# ( Name )	Flags	Channelbits	BcnIntvl
<gps-point bssid="00:01:E3:D2:F3:1B" source="00:01:E3:D2:F3:19" time-sec="1378290310" time-usec="122203" lat="52.456932" lon="5.876672" spd="4.213000" heading="215.389999" fix="3" alt="1.400000" signal_dbm="-69" noise_dbm="0"/>
N 50.8414667;E 4.3660500;( bombolong );ad-hoc;( 02:02:cf:87:27:b5 );01:00:00 (GMT);[  76  ];# ( NULL );0002;0002;
bssid	lat	lon
MAC,SSID,AuthMode,FirstSeen,Channel,RSSI,CurrentLatitude,CurrentLongitude,AltitudeMeters,AccuracyMeters,Type
"""

def print_as_tsv(file, parse_line):
    print "# BSSID\tTimestamp\tLatitude\tLongitude\tAccuracy\tAltitude\tAltitude_Accuracy\tChannel\tSignal_dBm\tSSID"
    for line in file:
        ap = parse_line(line.strip())
        if ap is not None:
            print_ap(ap)
