stumbler-tsv is a collection of Python scripts to convert a variety of Wi-Fi stumblers' file formats into a common file format that can be more easily imported by the [Mozilla Ichnaea](https://github.com/mozilla/ichnaea/) geolocation service.

# Instructions

```
./tsv/tsv_gmon.py tests/gmon.txt
./tsv/tsv_iphone_consolidated_db.py tests/iphone_consolidated_db.csv
./tsv/tsv_kismet_gpsxml.py tests/kismet.gpsxml
./tsv/tsv_ns1.py tests/kismac.ns1
./tsv/tsv_ns1.py tests/wealy.ns2
./tsv/tsv_wififofum_kml.py tests/wififofum.kml
./tsv/tsv_wigle_csv.py tests/wigle.csv
./tsv/tsv_wigle_kml.py tests/wigle.kml
```

# File Format

A `.tsv` file contains rows of tab-separated values. Lines beginning with the `#` character are comments. Some rows may be missing some column values; these values are represented as a zero-length string between the tab separators. The first line of `.tsv` file is usually a comment with tab-separated column names:

`# BSSID	Timestamp	Latitude	Longitude	Accuracy	Altitude	Altitude_Accuracy	Channel	Signal_dBm	SSID`

* _BSSID_ is a colon-separated MAC address using lowercase hexadecimal numbers with leading zeros like `01:23:45:67:89:ab`. Some stumblers use uppercase hexadecimal, skip leading zeros, or use a `-` separater or none at all.
* _Timestamp_ is the nonnegative number of seconds since 1970-01-01Z00:00:00 (aka `time_t`). `0` is may be used to indicate a bogus or missing timestamp value.
* _Latitude_ is an arbitrary precision floating-point number. `0` is technically a valid latitude, but it more likely indicates a bogus measurement.
* _Longitude_ is an arbitrary precision floating-point number. `0` is technically a valid longitude, but it more likely indicates a bogus measurement.
* _Accuracy_ is the radius (in nonnegative meters) from the likely location, so a smaller radius is more accurate. `0` is probably a bogus accuracy value and should be treated as a missing value.
* _Altitude_ is the altitude (in meters) of the measurement. Many devices report bogus altitude measurements (like -20 km or 400 km!) or only positive measurements, so altitude values are not trustworthy.
* _Altitude Accuracy_ is distance (in nonnegative meters) from the likely altitude, so smaller distance is more accurate.
* _Channel_ is the Wi-Fi channel of the access point. Some access points or stumblers report bogus channel numbers, so these values are untrustworthy.
* _Signal dBm_ is the measured signal strength (in [dBm](https://en.wikipedia.org/wiki/DBm)). Typical values are in the range -100 to -10 dBm, but some devices report bogus values far out of the typical range. Signal strength is notoriously untrustworthy and should probably not be used to estimate distance to an access point. Walls and human bodies often have a greater attenuation effect than distance!
* _SSID_ is the human-readable network name. SSIDs are strings of 0 to 32 bytes. SSIDs do not specify a character encoding, so many stumblers will corrupt SSIDs that contain "fancy" high ASCII or multibyte characters. Access points can elect to "hide" their SSID by not broadcasting it, which is technically different than a zero-length SSID string, but our tab-separated format does not distinguish these SSIDs. Google recommends that users who do not want their access points mapped should append the string `_nomap` to the end of their SSIDs, so `My Wi-Fi Network` would become `My Wi-Fi Network_nomap`.

# TODO
* Implement tsv_kismet_csv.py
* Implement tsv_openwlanmap.py
* Fix tsv_kismet_gpsxml.py parsing
* Fix tsv_wigle_kml.py parsing of BSSIDs like "31040410_56978_2731527"
