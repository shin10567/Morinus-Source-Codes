# -*- coding: utf-8 -*-
import json
import urllib.request as urllib2
import urllib
from datetime import datetime, timezone
try:
	from zoneinfo import ZoneInfo            # Py3.9+
except Exception:
	try:
		from backports.zoneinfo import ZoneInfo  # Py3.7–3.8
	except Exception:
		ZoneInfo = None

try:
	from timezonefinder import TimezoneFinder
except Exception:
	TimezoneFinder = None

#Csaba's code

class Geonames:
	NAME, LON, LAT, COUNTRYCODE, COUNTRYNAME, ALTITUDE, GMTOFFS = range(0, 7)
	_tf = None
	username='morinus'
	langs = ("en", "hu", "it", "fr", "ru", "es","en","en","en")

	def __init__(self, city, maxnum, langid):
		self.city = city
		if Geonames._tf is None and TimezoneFinder is not None:
			try:
				Geonames._tf = TimezoneFinder()
			except Exception:
				Geonames._tf = None

		self.maxnum = maxnum
		self.langid = langid
		self.li = None


	def fetch_values_from_page(self, url, params, key):
		url = url % urllib.parse.urlencode(params)

		try:
			page = urllib2.urlopen(url)
			doc = json.loads(page.read())
			values = doc.get(key, None)
		except Exception as e:
			values = None
#			print(e)

		return values


	def get_basic_info(self, city):
		url = "http://api.geonames.org/searchJSON?%s"

		params = {
			"username" : self.username,
			"lang" : Geonames.langs[self.langid],
			"q" : city,
			"featureClass" : "P",
			"maxRows" : self.maxnum,
			"orderby" : "relevance"    # ← 추가(선택사항, 지원되면 상위가 더 빨리 뜸)
		}

		return self.fetch_values_from_page(url, params, "geonames")

	def get_gmt_offset_offline(self, longitude, latitude, when_utc=None):
		"""
		TimezoneFinder + (backports.)zoneinfo 로 오프라인 오프셋(시간대 오프셋, '시간' 단위) 계산.
		- when_utc가 주어지면: 그 UTC 시각에서의 '총 오프셋'(DST 포함)을 반환
		- when_utc가 None이면: '표준시(raw offset, DST 제외)'을 추정하여 반환
		실패 시 None 반환.
		"""
		if Geonames._tf is None or ZoneInfo is None:
			return None
		try:
			lon = float(longitude); lat = float(latitude)
		except Exception:
			return None

		# 가장 적합한 타임존 이름 추출
		try:
			tzname = Geonames._tf.timezone_at(lng=lon, lat=lat)
			if not tzname:
				tzname = Geonames._tf.closest_timezone_at(lng=lon, lat=lat)
		except Exception:
			tzname = None
		if not tzname:
			return None

		try:
			tz = ZoneInfo(tzname)
		except Exception:
			return None

		from datetime import datetime, timezone as _tz

		# when_utc가 주어졌다면: 그 시각의 총 오프셋(DST 포함)
		if when_utc is not None:
			if when_utc.tzinfo is None:
				when_utc = when_utc.replace(tzinfo=_tz.utc)
			else:
				when_utc = when_utc.astimezone(_tz.utc)
			off = when_utc.astimezone(tz).utcoffset()
			return None if off is None else (off.total_seconds() / 3600.0)

		# when_utc가 None이면: '표준시(raw offset)'을 계산
		# 방법: 기준 연도(예: 2024)의 각 달 1일 12:00 UTC를 해당 타임존으로 변환해
		#      12개의 utcoffset 중 '가장 작은 값(보통 DST 미적용 표준시)'을 선택
		def _std_off_hours(tzobj):
			year = 2024
			offs = []
			for m in range(1, 13):
				dt_utc = datetime(year, m, 1, 12, tzinfo=_tz.utc)
				off = dt_utc.astimezone(tzobj).utcoffset()
				if off is not None:
					offs.append(off.total_seconds() / 3600.0)
			if not offs:
				return None
			# 예: 뉴욕(-5, -4) → min = -5 (표준시), 런던(0, +1) → 0, 시드니(+10, +11) → +10
			return min(offs)

		offh = _std_off_hours(tz)
		return offh

	def get_gmt_offset(self, longitude, latitude):
		# 1) 오프라인 계산 먼저 시도
		off = self.get_gmt_offset_offline(longitude, latitude)
		if off is not None:
			return off
		url = "http://api.geonames.org/timezoneJSON?%s"
		params = {
			"username" : self.username,
			"lng" : longitude,
			"lat" : latitude
			}
		return self.fetch_values_from_page(url, params, "rawOffset")


	def get_elevation(self, longitude, latitude):
		url = "http://api.geonames.org/astergdemJSON?%s"
		params = {
			"username" : self.username,
			"lng" : longitude,
			"lat" : latitude
			}
		return self.fetch_values_from_page(url, params, "astergdem")


	def get_location_info(self):
		info = self.get_basic_info(self.city)

		if not info:
			return False

		self.li = []
		for it in info:
			longitude = it.get("lng", 0)
			latitude = it.get("lat", 0)
			placename = it.get("name", "")
			country_code = it.get("countryCode", "")
			country_name = it.get("countryName", "")

			gmt_offset = None
			elevation  = None

			self.li.append((placename, float(longitude), float(latitude), 
				country_code, country_name, elevation, gmt_offset))

		return True



