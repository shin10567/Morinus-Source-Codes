# -*- coding: utf-8 -*-
"""Positions for Date (Secondary Progressions by real date)

규칙(요약):
- 1년(현실) = 1일(에피메리스)
- 1일(현실) = 1/365 or 1/366 (그레고리 윤년)
- 행성: 분수일 그대로(스위스에페메리스 보간/계산 그대로)
- 감응점(Asc/MC/커스프 등): '정수년(=정수 에피메리스 일)'과 그 다음 1일 사이 이동량을
  365/366으로 나눠 선형 보간
- LoF: 보간된 Asc 기준으로 주/야 판정 후, 보간된 Asc로 재계산
"""

import math
import calendar

import astrology
import chart
import houses
import planets
import util


def _signed_shortest_angle_delta(a1, a0):
    """Return signed delta (a1-a0) wrapped to (-180, 180]."""
    d = float(a1) - float(a0)
    if d > 180.0:
        d -= 360.0
    elif d <= -180.0:
        d += 360.0
    return d


def _cotrans_lon_to_equ(lon, obl):
    ra, decl, _ = astrology.swe_cotrans(float(lon), 0.0, 1.0, -float(obl))
    return float(ra), float(decl)


def _obl_ut(jd_ut):
    d = astrology.swe_deltat(jd_ut)
    serr, x = astrology.swe_calc(jd_ut + d, astrology.SE_ECL_NUT, 0)
    return float(x[0])


def _ayan_ut(jd_ut, options):
    if getattr(options, 'ayanamsha', 0) != 0:
        astrology.swe_set_sid_mode(options.ayanamsha - 1, 0, 0)
        return float(astrology.swe_get_ayanamsa_ut(jd_ut))
    return 0.0


def _build_interpolated_houses(jd_base, jd_next, frac, place, options, obl_final, ayan_final):
    """Create a Houses instance at jd_base, then overwrite with interpolated values."""
    hflag = 0

    obl0 = _obl_ut(jd_base)
    obl1 = _obl_ut(jd_next)
    ay0 = _ayan_ut(jd_base, options)
    ay1 = _ayan_ut(jd_next, options)

    hb = houses.Houses(jd_base, hflag, place.lat, place.lon, options.hsys, obl0, options.ayanamsha, ay0)
    hn = houses.Houses(jd_next, hflag, place.lat, place.lon, options.hsys, obl1, options.ayanamsha, ay1)

    # Start with a fresh houses object (same time system), then overwrite.
    hout = houses.Houses(jd_base, hflag, place.lat, place.lon, options.hsys, obl_final, options.ayanamsha, ayan_final)

    # --- interpolate cusps ---
    cusps = [0.0] * (houses.Houses.HOUSE_NUM + 1)
    cusps[0] = 0.0
    for i in range(1, houses.Houses.HOUSE_NUM + 1):
        d = _signed_shortest_angle_delta(hn.cusps[i], hb.cusps[i])
        cusps[i] = util.normalize(hb.cusps[i] + d * frac)

    # Whole sign sidereal special-case (Morinus 기존 정책 유지)
    if getattr(options, 'ayanamsha', 0) != 0 and options.hsys == 'W':
        # Houses.__init__의 로직을 재현: sid asc = tropical asc - ayan
        asc_sid = util.normalize(hb.ascmc[houses.Houses.ASC] - ayan_final)
        sign = int(asc_sid / 30.0)
        for i in range(houses.Houses.HOUSE_NUM):
            cusps[i + 1] = util.normalize((sign + i) * 30.0 + ayan_final)

    # --- interpolate ascmc array (ASC/MC 포함) ---
    ascmc = [0.0] * len(hb.ascmc)
    for j in range(len(ascmc)):
        d = _signed_shortest_angle_delta(hn.ascmc[j], hb.ascmc[j])
        ascmc[j] = util.normalize(hb.ascmc[j] + d * frac)

    # Write back
    hout.obl = float(obl_final)
    hout.cusps = tuple(cusps)
    hout.ascmc = tuple(ascmc)

    # ascmc2: (ASC lon/lat/RA/decl, MC lon/lat/RA/decl)
    asc_lon = hout.ascmc[houses.Houses.ASC]
    mc_lon = hout.ascmc[houses.Houses.MC]
    asc_ra, asc_decl = _cotrans_lon_to_equ(asc_lon, obl_final)
    mc_ra, mc_decl = _cotrans_lon_to_equ(mc_lon, obl_final)
    hout.ascmc2 = ((asc_lon, 0.0, asc_ra, asc_decl), (mc_lon, 0.0, mc_ra, mc_decl))

    # Regiomontanus MP values
    try:
        qasc = math.degrees(math.asin(math.tan(math.radians(asc_decl)) * math.tan(math.radians(place.lat))))
    except Exception:
        qasc = 0.0
    hout.regioMPAsc = asc_ra - qasc
    hout.regioMPMC = mc_ra

    # cusps2 + cuspstmp
    hout.cuspstmp = [[0.0, 0.0] for _ in range(houses.Houses.HOUSE_NUM)]
    cusps2 = []
    for i in range(houses.Houses.HOUSE_NUM):
        ra, decl = _cotrans_lon_to_equ(hout.cusps[i + 1], obl_final)
        hout.cuspstmp[i][0] = ra
        hout.cuspstmp[i][1] = decl
        cusps2.append((ra, decl))
    hout.cusps2 = tuple(cusps2)

    return hout


def make_progressed_chart_by_real_date(radix_chart, options, yy, mm, dd):
    """Build a progressed chart for a real date using the requested Positions for Date rules.

    Returns:
        (age_int_years, age_years_float, progressed_date_tuple, progressed_chart)
    """
    nt = radix_chart.time

    # UT anchor fixed to radix UT
    try:
        ut_anchor = float(nt.time)
    except Exception:
        ut_anchor = float(nt.hour) + float(nt.minute) / 60.0 + float(nt.second) / 3600.0

    birth_jd = float(nt.jd)
    calflag = astrology.SE_JUL_CAL if nt.cal == chart.Time.JULIAN else astrology.SE_GREG_CAL

    # --- real date → age (years + fraction) ---
    target_jd = astrology.swe_julday(int(yy), int(mm), int(dd), ut_anchor, calflag)

    by, bm, bd, _ = astrology.swe_revjul(birth_jd, calflag)
    ty, tm, td, _ = astrology.swe_revjul(target_jd, calflag)

    anniv_year = ty if (tm, td) >= (bm, bd) else (ty - 1)
    anniv_day = 28 if (bm == 2 and bd == 29 and not calendar.isleap(int(anniv_year))) else int(bd)
    anniv_jd = astrology.swe_julday(int(anniv_year), int(bm), int(anniv_day), ut_anchor, calflag)

    years_passed = int(anniv_year) - int(by)
    days_in_year = 366.0 if calendar.isleap(int(anniv_year)) else 365.0
    remainder_days = float(target_jd - anniv_jd)
    frac_year = remainder_days / days_in_year
    if frac_year < 0.0:
        # anniv 정의상 이론적으로는 안 나와야 하지만 안전장치
        frac_year = 0.0
    elif frac_year >= 1.0:
        # 안전하게 클램프
        frac_year = max(0.0, min(0.999999999, frac_year))

    age_years = float(years_passed) + float(frac_year)

    # --- progressed planets time (fractional ephemeris day) ---
    jd_prog = birth_jd + age_years
    py, pm, pd, ptime = astrology.swe_revjul(jd_prog, calflag)
    ph = int(ptime)
    pmi = int((ptime - ph) * 60.0 + 1e-6)
    ps = int(round(((ptime - ph) * 60.0 - pmi) * 60.0))

    tm_prog = chart.Time(int(py), int(pm), int(pd), ph, pmi, ps, False, nt.cal,
                         chart.Time.GREENWICH, True, 0, 0, False, radix_chart.place, False)
    prg = chart.Chart(radix_chart.name, radix_chart.male, tm_prog, radix_chart.place,
                      chart.Chart.TRANSIT, '', options, False)

    # --- interpolate sensitive points within the year band ---
    # base = integer years, next = +1 day (always 'forward movement')
    jd_base = birth_jd + float(years_passed)
    jd_next = jd_base + 1.0

    # ensure topo settings match Chart.create policy
    if getattr(options, 'topocentric', False):
        try:
            astrology.swe_set_topo(radix_chart.place.lon, radix_chart.place.lat, radix_chart.place.altitude)
        except Exception:
            pass

    obl_final = _obl_ut(jd_prog)
    ayan_final = _ayan_ut(jd_prog, options)

    prg.houses = _build_interpolated_houses(jd_base, jd_next, frac_year, prg.place, options, obl_final, ayan_final)

    # raequasc from interpolated EQUASC
    try:
        raeq, _dec, _dist = astrology.swe_cotrans(prg.houses.ascmc[houses.Houses.EQUASC], 0.0, 1.0, -obl_final)
        prg.raequasc = float(raeq)
    except Exception:
        pass

    # rebuild planets with interpolated ascmc2/raequasc so speculums align
    try:
        pflag = astrology.SEFLG_SWIEPH | astrology.SEFLG_SPEED
        if getattr(options, 'topocentric', False):
            pflag |= astrology.SEFLG_TOPOCTR
        if getattr(options, 'ayanamsha', 0) != 0:
            astrology.swe_set_sid_mode(options.ayanamsha - 1, 0, 0)
            prg.ayanamsha = float(astrology.swe_get_ayanamsa_ut(jd_prog))

        prg.planets = planets.Planets(jd_prog, options.meannode, pflag, prg.place.lat,
                                      prg.houses.ascmc2, prg.raequasc, prg.nolat, obl_final)
    except Exception:
        pass

    # Recompute LoF using interpolated ASC and day/night based on that ASC
    try:
        prg.calcFortune()
    except Exception:
        pass

    return years_passed, age_years, (int(py), int(pm), int(pd)), prg