
# -*- coding: utf-8 -*-
import math
import astrology
import chart
import planets
import mtexts
import util
import math
ANGLE_LABELS = ('Asc','MC','Dsc','IC')

class RiseSet:
    """Computes Rise/Set times (for the birthday)"""

    RISE, MC, SET, IC = range(0, 4)

    Angles = [astrology.SE_CALC_RISE, astrology.SE_CALC_MTRANSIT , astrology.SE_CALC_SET,  astrology.SE_CALC_ITRANSIT]

    def __init__(self, jd, cal, lon, lat, alt, tz_hours, pls):
        self.jd = jd
        self.cal = cal
        self.lon = lon
        self.lat = lat
        self.alt = alt

        self.calflag = astrology.SE_GREG_CAL
        if self.cal == chart.Time.JULIAN:
            self.calflag = astrology.SE_JUL_CAL
        self.tz_offs_days = float(tz_hours) / 24.0
        #self.offs = lon*4.0/1440.0

        self.times = []

        self.calcTimes()
    
#		self.printRiseSet(pls)


    def calcTimes(self):
        #the date we get from julianday is the same as year, month day in Time-class but we didn't pass it to the init function.
        oyear, omonth, oday, otim = astrology.swe_revjul(self.jd, self.calflag)
        lyear, lmonth, lday, _ = astrology.swe_revjul(self.jd + self.tz_offs_days, self.calflag)
        t0 = self.jd - 1.0
        t1 = self.jd + 1.0
        numangles = len(RiseSet.Angles)
        for i in range(planets.Planets.PLANETS_NUM):#Nodes are excluded
            ar = []
            pick = {k: None for k in ANGLE_LABELS}  
            # ---- Fallback: 파란으로 못 잡은 각은 Swiss Ephemeris로 보강 ----
            SWISS_KIND = {'Asc': astrology.SE_CALC_RISE,
                        'MC':  astrology.SE_CALC_MTRANSIT,
                        'Dsc': astrology.SE_CALC_SET,
                        'IC':  astrology.SE_CALC_ITRANSIT}

            for key in ANGLE_LABELS:
                if pick[key] is not None:
                    continue

                best_ut = None
                best_err = 1e9
                # swe_rise_trans는 앞으로만 찾으므로 씨드 두 개에서 시도
                for seed in (self.jd - 1.0, self.jd):
                    ret, tut, serr = astrology.swe_rise_trans(
                        seed, i, '', astrology.SEFLG_SWIEPH,
                        SWISS_KIND[key] | astrology.SE_BIT_DISC_CENTER | astrology.SE_BIT_NO_REFRACTION,
                        self.lon, self.lat, float(self.alt), 0.0, 0.0
                    )
                    if ret >= 0:
                        # 표준시 ‘같은 날’을 우선 반영
                        y, m, d, _ = astrology.swe_revjul(tut + self.tz_offs_days, self.calflag)
                        if (y == lyear and m == lmonth and d == lday):
                            pick[key] = tut
                            break
                        # 같은 날이 아니면, 그래도 가장 가까운 걸 후보로
                        err = abs(tut - self.jd)
                        if err < best_err:
                            best_err, best_ut = err, tut
                if pick[key] is None and best_ut is not None:
                    pick[key] = best_ut
            # ---- /Fallback ----

            for key in ANGLE_LABELS:
                if pick[key] is None:
                    hr = 0.0
                else:
                    _, _, _, hr = astrology.swe_revjul(pick[key] + self.tz_offs_days, self.calflag)
                ar.append(hr)

            self.times.append(ar)


    def printRiseSet(self, pls):
        numangles = len(RiseSet.Angles)
        txt = [mtexts.txtsriseset['Rise'], mtexts.txtsriseset['MC'], mtexts.txtsriseset['Set'], mtexts.txtsriseset['IC']]
        print ('')
        print ('Rise/Set times:')
        for i in range(planets.Planets.PLANETS_NUM):#Nodes are excluded
            for angle in range(numangles):
                h,m,s = util.decToDeg(self.times[i][angle])
                print ("%s: %s: %02d:%02d:%02d" % (pls.planets[i].name, txt[angle], h, m, s))



