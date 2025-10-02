
# -*- coding: utf-8 -*-
import astrology
import chart
import util
import mtexts


class ProfectionsMonthly:
	def __init__(self, pchrts, step12, rownum):
		self.dates = []

		y = pchrts[0][1]+rownum
		m = pchrts[0][2]
		d = pchrts[0][3]
		if (not util.checkDate(y, m, d)):
			y, m, d = util.incrDay(y, m, d)

		#calc
		dat = (y, m, d)
		self.dates.append(dat)

		idx = 12
		mon = 30.4368492
		if not step12:
			idx = 13
			mon = 28.0955531

		calflag = astrology.SE_GREG_CAL
		if pchrts[0][0].time.cal == chart.Time.JULIAN:
			calflag = astrology.SE_JUL_CAL
		jdval = astrology.swe_julday(int(y), int(m), int(d), pchrts[0][0].time.time, calflag)

		# 균등 12/13 분할: 나머지 없음
		SOLAR_YEAR = 365.2421904
		self.dates = []

		if step12:
			# 12칸: 시작일 포함 → 총 12개 (i=0..11)
			for i in range(0, 12):
				jd_i = jdval + SOLAR_YEAR * (i / 12.0)
				jy, jm, jd_day, jh = astrology.swe_revjul(jd_i, calflag)
				self.dates.append((jy, jm, jd_day))
		else:
			# 13칸: 시작일 포함 → 총 13개 (i=0..12)
			for i in range(0, 13):
				jd_i = jdval + SOLAR_YEAR * (i / 13.0)
				jy, jm, jd_day, jh = astrology.swe_revjul(jd_i, calflag)
				self.dates.append((jy, jm, jd_day))




