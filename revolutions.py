# -*- coding: utf-8 -*-
import astrology
import mtexts
import transits
import util

def compute_solar_at_year(self, chrt, target_year):
    """지정 연도의 솔라 리턴 한 방 호출"""
    by = target_year   # 시작 기준년은 그냥 target_year로
    bm = chrt.time.month
    bd = chrt.time.day
    return self.compute(Revolutions.SOLAR, by, bm, bd, chrt, target_year=target_year)

class Revolutions:
    SOLAR = 0
    LUNAR = 1
    MERCURY = 2
    VENUS = 3
    MARS = 4
    JUPITER = 5
    SATURN = 6


    def __init__(self):
        self.t = [0, 0, 0, 0, 0, 0]


    # 기존 시그니처
    # def compute(self, typ, by, bm, bd, chrt):

    # ── 변경: 선택 인자 target_year 추가
    def compute(self, typ, by, bm, bd, chrt, target_year=None):
        if typ == Revolutions.SOLAR:
            # ① 연도 결정
            if target_year is not None:
                year = int(target_year)
            else:
                year = by
                if bm > chrt.time.month or (bm == chrt.time.month and bd > chrt.time.day):
                    year += 1

            # ② 이하 기존 로직 유지
            month = chrt.time.month
            day = chrt.time.day

            trans = transits.Transits()
            trans.month(year, month, chrt, astrology.SE_SUN)

            if len(trans.transits) == 0:
                if day < 4:
                    year, month = util.decrMonth(year, month)
                else:
                    year, month = util.incrMonth(year, month)
                trans = transits.Transits()
                trans.month(year, month, chrt, astrology.SE_SUN)

            if len(trans.transits) > 0:
                self.createRevolution(year, month, trans)
                return True
            return False
        # 나머지 LUNAR~SATURN 분기는 그대로...

        elif typ == Revolutions.LUNAR:
            trans = transits.Transits()
            trans.month(by, bm, chrt, astrology.SE_MOON)

            if len(trans.transits) > 0:
                second = False

                if bd > trans.transits[0].day:
                    # There can be more than one lunar in a month!!
                    if len(trans.transits) > 1:
                        if bd > trans.transits[1].day:
                            by, bm = util.incrMonth(by, bm)

                            trans = transits.Transits()
                            trans.month(by, bm, chrt, astrology.SE_MOON)
                        else:
                            second = True
                    else:
                        by, bm = util.incrMonth(by, bm)

                        trans = transits.Transits()
                        trans.month(by, bm, chrt, astrology.SE_MOON)

                if len(trans.transits) > 0:
                    if second:
                        self.createRevolution(by, bm, trans, 1)
                    else:
                        self.createRevolution(by, bm, trans)
                    return True

            return False
        elif typ == Revolutions.MERCURY:
            for i in range(14):
                trans = transits.Transits()
                trans.month(by, bm, chrt, astrology.SE_MERCURY)

                if len(trans.transits) > 0:
                    if not (i == 0 and bd > trans.transits[0].day):
                        self.createRevolution(by, bm, trans)
                        return True

                by, bm = util.incrMonth(by, bm)

            return False
        elif typ == Revolutions.VENUS:
            for i in range(16):
                trans = transits.Transits()
                trans.month(by, bm, chrt, astrology.SE_VENUS)

                if len(trans.transits) > 0:
                    if not (i == 0 and bd > trans.transits[0].day):
                        self.createRevolution(by, bm, trans)
                        return True

                by, bm = util.incrMonth(by, bm)

            return False
        elif typ == Revolutions.MARS:
            for i in range(26):
                trans = transits.Transits()
                trans.month(by, bm, chrt, astrology.SE_MARS)

                if len(trans.transits) > 0:
                    if not (i == 0 and bd > trans.transits[0].day):
                        self.createRevolution(by, bm, trans)
                        return True

                by, bm = util.incrMonth(by, bm)

            return False
        elif typ == Revolutions.JUPITER:
            for i in range(12*12):
                trans = transits.Transits()
                trans.month(by, bm, chrt, astrology.SE_JUPITER)

                if len(trans.transits) > 0:
                    if not (i == 0 and bd > trans.transits[0].day):
                        self.createRevolution(by, bm, trans)
                        return True

                by, bm = util.incrMonth(by, bm)

            return False
        elif typ == Revolutions.SATURN:
            for i in range(30*12):
                trans = transits.Transits()
                trans.month(by, bm, chrt, astrology.SE_SATURN)

                if len(trans.transits) > 0:
                    if not (i == 0 and bd > trans.transits[0].day):
                        self.createRevolution(by, bm, trans)
                        return True

                by, bm = util.incrMonth(by, bm)

            return False

        return False


    def createRevolution(self, year, month, trans, num = 0):
        self.t[0] = year
        self.t[1] = month
        self.t[2] = trans.transits[num].day
        h, m, s = util.decToDeg(trans.transits[num].time)
        self.t[3] = h
        self.t[4] = m
        self.t[5] = s



