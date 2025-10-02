# -*- coding: utf-8 -*-
from __future__ import division
import wx, math
import os
import io
import astrology
import util
from PIL import Image, ImageDraw, ImageFont
import commonwnd as cw
import mtexts
try:
    import sweastrology as swe
except ImportError:
    swe = None

DEG = math.pi/180.0
SID_RATE = 1.002737909350795  # sidereal hours per UT hour
ANGLE_TOL_MIN = 2.0   # 분; 앵글 회합 정의의 허용 창(±2분)
# ---- fixstars.cat fallback ----
# ---- fixstars.cat fallback with proper motion ----
PM_UNITS = 'per_century'  # 대부분의 fixstars.cat: RA는 "초/세기", Dec는 "초각/세기"
# 필요시 'per_year' 로 바꾸면 연단위 μ로 처리됨.

_FIXSTAR_CAT_DB = None

def _load_fixstars_cat():
    """
    fixstars.cat을 찾아 1회 캐시 로드:
      code -> {name, ra_j2000_deg, dec_j2000_deg, pm_ra_sec, pm_dec_arcsec}
    pm_ra_sec   : RA 고유운동 (초/세기 또는 초/년) — PM_UNITS로 단위 지정
    pm_dec_arcsec: Dec 고유운동 (초각/세기 또는 초각/년)
    """
    import os
    global _FIXSTAR_CAT_DB
    if _FIXSTAR_CAT_DB is not None:
        return _FIXSTAR_CAT_DB

    paths = []
    try:
        import common
        ep = getattr(common.common, 'ephepath', '')
        if ep:
            paths += [os.path.join(ep, 'fixstars.cat'),
                      os.path.join(ep, 'SWEP', 'Ephem', 'fixstars.cat')]
    except Exception:
        pass
    here = os.path.dirname(__file__)
    paths += [os.path.join(here, 'SWEP', 'Ephem', 'fixstars.cat'),
              os.path.join(here, 'fixstars.cat')]

    db = {}
    for path in paths:
        if not os.path.isfile(path):
            continue
        try:
            with open(path, 'r') as f:
                for line in f:
                    s = line.strip()
                    if not s or s.startswith('#'):
                        continue
                    parts = [p.strip() for p in s.split(',')]
                    # 형식 예(최소): name, code, mag, RAh, RAm, RAs, DEd, DEm, DEs, [pmRA, pmDE]
                    if len(parts) < 9:
                        continue
                    name = parts[0]
                    code = parts[1].lstrip(',')
                    # RA
                    try:
                        ra_h = float(parts[3]); ra_m = float(parts[4]); ra_s = float(parts[5])
                    except:
                        continue
                    ra_deg = (ra_h + ra_m/60.0 + ra_s/3600.0) * 15.0
                    # Dec (부호 처리)
                    try:
                        dec_d_raw = parts[6]
                        dec_d = abs(float(dec_d_raw))
                        dec_m = float(parts[7]); dec_s = float(parts[8])
                        sign = -1.0 if str(dec_d_raw).strip().startswith('-') else 1.0
                    except:
                        continue
                    dec_deg = sign * (dec_d + dec_m/60.0 + dec_s/3600.0)
                    # Proper motion (있으면 읽고, 없으면 0)
                    pm_ra_sec = 0.0
                    pm_dec_arcsec = 0.0
                    if len(parts) >= 11:
                        try:
                            pm_ra_sec = float(parts[9])     # RA: 초(시간) / 세기(또는 연)
                            pm_dec_arcsec = float(parts[10]) # Dec: 초각 / 세기(또는 연)
                        except:
                            pm_ra_sec = 0.0; pm_dec_arcsec = 0.0
                    db[code] = {
                        'name': name,
                        'ra_j2000_deg': ra_deg,
                        'dec_j2000_deg': dec_deg,
                        'pm_ra_sec': pm_ra_sec,
                        'pm_dec_arcsec': pm_dec_arcsec
                    }
            _FIXSTAR_CAT_DB = db
            return _FIXSTAR_CAT_DB
        except Exception:
            continue
    _FIXSTAR_CAT_DB = {}
    return _FIXSTAR_CAT_DB

def _precess_eq_j2000_to_date(ra_deg, dec_deg, jd_ut):
    """IAU 1976 precession (J2000 -> of-date), 근사."""
    T = (jd_ut - 2451545.0)/36525.0
    zeta = (2306.2181 + 1.39656*T - 0.000139*T*T)*T + (0.30188 - 0.000344*T)*T*T + 0.017998*T*T*T
    z    = (2306.2181 + 1.39656*T - 0.000139*T*T)*T + (1.09468 + 0.000066*T)*T*T + 0.018203*T*T*T
    theta= (2004.3109 - 0.85330*T - 0.000217*T*T)*T - (0.42665 + 0.000217*T)*T*T - 0.041833*T*T*T
    zeta *= (math.pi/(180.0*3600.0)); z *= (math.pi/(180.0*3600.0)); theta *= (math.pi/(180.0*3600.0))
    a = ra_deg*DEG; d = dec_deg*DEG
    A = math.cos(d)*math.sin(a + zeta)
    B = math.cos(theta)*math.cos(d)*math.cos(a + zeta) - math.sin(theta)*math.sin(d)
    C = math.sin(theta)*math.cos(d)*math.cos(a + zeta) + math.cos(theta)*math.sin(d)
    ra2 = (math.atan2(A, B) + z) % (2.0*math.pi)
    dec2= math.asin(C)
    return ra2/DEG, dec2/DEG

def _apply_proper_motion_j2000(ra_deg, dec_deg, jd_ut, pm_ra_sec, pm_dec_arcsec):
    """
    J2000에서 of-date까지 고유운동 1차 보정.
    pm_ra_sec      : RA 시간초 / 세기(or 년) - PM_UNITS로 단위 지정
    pm_dec_arcsec  : Dec 초각 / 세기(or 년)
    반환: (ra_pm_deg, dec_pm_deg) — 여전히 J2000 기준 성좌에서의 위치(세차 전)
    """
    years = (jd_ut - 2451545.0)/365.25
    factor = (years/100.0) if PM_UNITS == 'per_century' else years
    dRA_deg  = (pm_ra_sec * factor) / 240.0   # 1초(시간) = 15″ = 1/240 도
    dDE_deg  = (pm_dec_arcsec * factor) / 3600.0
    ra1 = (ra_deg + dRA_deg) % 360.0
    dec1 = max(-90.0, min(90.0, dec_deg + dDE_deg))
    return ra1, dec1

def _ra_dec_star_deg_ut_from_cat(jd_ut, star_code):
    """
    fixstars.cat 로드 → (J2000 RA/Dec + μ 보정) → of-date 세차 반영 좌표 반환
    """
    code = star_code.lstrip(',')
    db = _load_fixstars_cat()
    if code not in db:
        raise RuntimeError(u"fixstars.cat에 항성 코드가 없습니다: %s" % code)
    ra0 = db[code]['ra_j2000_deg']
    de0 = db[code]['dec_j2000_deg']
    pmra = db[code].get('pm_ra_sec', 0.0)
    pmde = db[code].get('pm_dec_arcsec', 0.0)
    # 1) 고유운동(μ) 보정
    ra1, de1 = _apply_proper_motion_j2000(ra0, de0, jd_ut, pmra, pmde)
    # 2) of-date 세차 반영
    return _precess_eq_j2000_to_date(ra1, de1, jd_ut)
# ---- /fixstars.cat fallback with proper motion ----

# ====== 유틸 ======
def _norm24(x):
    x = x % 24.0
    return x + 24.0 if x < 0 else x

def _acos_clip(x):
    return math.acos(max(-1.0, min(1.0, x)))

def _fmt_deltat_minutes(du_days):
    s = int(round(abs(du_days)*86400.0))
    m, s = divmod(s, 60)
    return u"±%d′%02d″" % (m, s)

def _auto_h0_deg_for(ipl, *_, **__):
    """기하학적 상승/저녁: 굴절·반지름 무시, 중심점이 ASC에 정확히 걸리는 순간(h=0°)."""
    return 0.0

def _star_display_name(star_id_with_comma, jd_ref):
    """표시용 이름: Swiss 가능시 Swiss, 아니면 fixstars.cat의 name."""
    try:
        if swe is not None:
            q = star_id_with_comma if star_id_with_comma.startswith(u',') else (u',' + star_id_with_comma)
            xx, name_or_err = swe.fixstar(q)
            if isinstance(name_or_err, (str, unicode if 'unicode' in dir(__builtins__) else str)):
                return (name_or_err.split(u',')[0]).strip()
    except Exception:
        pass
    # cat 폴백
    db = _load_fixstars_cat()
    return db.get(star_id_with_comma.lstrip(','), {}).get('name', star_id_with_comma.lstrip(','))

def _ra_dec_star_deg_ut(jd_ut, star_name):
    """해당 UT에서 항성의 적경/적위(deg). 우선 Swiss, 실패 시 fixstars.cat(+μ) 폴백."""
    # Python2/3 문자열 안전 처리
    try:
        base_str = basestring  # py2
    except Exception:
        base_str = str         # py3
    if swe is None:
        return _ra_dec_star_deg_ut_from_cat(jd_ut, star_name)
    iflag = astrology.SEFLG_SWIEPH | astrology.SEFLG_TRUEPOS | astrology.SEFLG_EQUATORIAL
    q = star_name if isinstance(star_name, base_str) else (u"%s" % star_name)
    if not q.startswith(u','):
        q = u',' + q
    try:
        xx, _ = swe.fixstar_ut(q, jd_ut, iflag)
        return xx[0], xx[1]
    except Exception:
        # sefstars.txt 없는 경우 등 → fixstars.cat(+μ) 폴백
        return _ra_dec_star_deg_ut_from_cat(jd_ut, q)

def _ra_dec_planet_deg_ut(jd_ut, ipl, lon_deg, lat_deg, alt_m=0.0):
    if swe is None:
        raise RuntimeError("Swiss Ephemeris가 필요합니다.")
    swe.swe_set_topo(lon_deg, lat_deg, alt_m)
    iflag = astrology.SEFLG_SWIEPH | astrology.SEFLG_EQUATORIAL | astrology.SEFLG_TOPOCTR
    err, xx = swe.swe_calc_ut(jd_ut, ipl, iflag)
    return xx[0], xx[1]

def _lst(jd_ut, lon_deg):
    return _norm24(swe.swe_sidtime(jd_ut) + lon_deg/15.0)

def _sunrise_sunset_for_local_day_geometric(Y, M, D, tz_hours, lon_deg, lat_deg, alt_m=0.0, gregflag=astrology.SE_GREG_CAL):

    """
    현지 달력일(Y-M-D)의 기하학적 일출/일몰(UT JD) 한 쌍을 반환.
    h0 = 0°, 굴절/반지름 무시. 없으면 (None, None).
    """
    if swe is None:
        raise RuntimeError("Swiss Ephemeris가 필요합니다.")
    jd_local0_ut = swe.julday(Y, M, D, 0.0, gregflag) - tz_hours/24.0

    phi = lat_deg*DEG

    def _event_near(jd0, kind):  # kind in {"rise","set"}
        # 정오를 기준으로 초기 α,δ를 얻고 목표 LST를 계산 → 고정점 반복
        ra, dec = _ra_dec_planet_deg_ut(jd0 + 0.5, swe.SUN, lon_deg, lat_deg, alt_m)
        dec_r = dec*DEG
        denom = math.cos(phi)*math.cos(dec_r)
        if abs(denom) < 1e-12:
            return None
        cosH0 = (-math.sin(phi)*math.sin(dec_r)) / denom  # h0=0°
        if not (-1.0 <= cosH0 <= 1.0):
            return None
        H0_deg = _acos_clip(cosH0)/DEG
        alpha_h = ra/15.0
        if kind == "rise":
            lst_target = _norm24(alpha_h - H0_deg/15.0)
        else:
            lst_target = _norm24(alpha_h + H0_deg/15.0)
        ut = jd0 + (((lst_target - _lst(jd0, lon_deg)) % 24.0) / SID_RATE)/24.0
        for _ in range(8):
            ra, dec = _ra_dec_planet_deg_ut(ut, swe.SUN, lon_deg, lat_deg, alt_m)
            dec_r = dec*DEG
            denom = math.cos(phi)*math.cos(dec_r)
            if abs(denom) < 1e-12:
                return None
            cosH0 = (-math.sin(phi)*math.sin(dec_r)) / denom
            if not (-1.0 <= cosH0 <= 1.0):
                return None
            H0_deg = _acos_clip(cosH0)/DEG
            alpha_h = ra/15.0
            if kind == "rise":
                lst_target = _norm24(alpha_h - H0_deg/15.0)
            else:
                lst_target = _norm24(alpha_h + H0_deg/15.0)
            lst_now = _lst(ut, lon_deg)
            dt_h = ((lst_target - lst_now) % 24.0) / SID_RATE
            if abs(dt_h) < (0.25/60.0):  # <15초면 수렴
                break
            ut += dt_h/24.0
        return ut

    # 현지 달력일 경계 안에 들어오는 일출/일몰을 찾아서 선택
    sunrise_cands, sunset_cands = [], []
    for k in (-1, 0, +1, +2):
        ut_r = _event_near(jd_local0_ut + k, "rise")
        ut_s = _event_near(jd_local0_ut + k, "set")
        if ut_r and (jd_local0_ut <= ut_r < jd_local0_ut + 1.0):
            sunrise_cands.append(ut_r)
        if ut_s and (jd_local0_ut <= ut_s < jd_local0_ut + 1.0):
            sunset_cands.append(ut_s)

    sr = min(sunrise_cands) if sunrise_cands else None
    ss = min(sunset_cands) if sunset_cands else None
    return sr, ss

ANGLE_LABELS = (u"Asc", u"MC", u"Dsc", u"IC")
def _load_sign_glyphs():
    import common
    for attr in ('Signs', 'Signs1', 'Signs2'):
        s = getattr(common.common, attr, None)
        if isinstance(s, (list, tuple)) and len(s) == 12:
            return s
    return (u'♈', u'♉', u'♊', u'♋', u'♌', u'♍', u'♎', u'♏', u'♐', u'♑', u'♒', u'♓')

def _load_planet_glyphs():
    import common
    for attr in ('Planets', 'Planets1', 'Planets2'):
        g = getattr(common.common, attr, None)
        if isinstance(g, (list, tuple)) and len(g) >= 10:
            return g
    # Sun..Pluto fallback (유니코드)
    return (u'☉', u'☽', u'☿', u'♀', u'♂', u'♃', u'♄', u'♅', u'♆', u'♇')

def _lst_target_for_kind(alpha_h, dec_r, phi, kind):
    k = (kind or u"").strip().lower()
    if k in ("asc", "dsc"):
        denom = math.cos(phi)*math.cos(dec_r)
        if abs(denom) < 1e-12:
            return None
        cosH0 = (-math.sin(phi)*math.sin(dec_r)) / denom  # h=0°
        if not (-1.0 <= cosH0 <= 1.0):
            return None
        H0_deg = _acos_clip(cosH0)/DEG
        return _norm24(alpha_h - H0_deg/15.0) if k == "asc" else _norm24(alpha_h + H0_deg/15.0)
    elif k == "mc":
        return _norm24(alpha_h)
    elif k == "ic":
        return _norm24(alpha_h + 12.0)
    return None

def _angle_times_planet_in(lon_deg, lat_deg, ipl, t0_ut, t1_ut, alt_m=0.0, max_iter=8):
    if swe is None:
        raise RuntimeError("Swiss Ephemeris가 필요합니다.")
    phi = lat_deg*DEG
    outs = []
    jd_days = range(int(math.floor(t0_ut)) - 1, int(math.floor(t1_ut)) + 2)
    for jd0 in jd_days:
        for kind in ANGLE_LABELS:
            ra, dec = _ra_dec_planet_deg_ut(jd0 + 0.5, ipl, lon_deg, lat_deg, alt_m)
            alpha_h = ra/15.0; dec_r = dec*DEG
            lst_tgt = _lst_target_for_kind(alpha_h, dec_r, phi, kind)
            if lst_tgt is None: 
                continue
            ut = jd0 + (((lst_tgt - _lst(jd0, lon_deg)) % 24.0) / SID_RATE) / 24.0
            for _ in range(max_iter):
                ra, dec = _ra_dec_planet_deg_ut(ut, ipl, lon_deg, lat_deg, alt_m)
                alpha_h = ra/15.0; dec_r = dec*DEG
                lst_tgt = _lst_target_for_kind(alpha_h, dec_r, phi, kind)
                if lst_tgt is None:
                    ut = None; break
                lst_now = _lst(ut, lon_deg)
                dt_h = ((lst_tgt - lst_now) % 24.0) / SID_RATE
                if abs(dt_h) < (0.25/60.0):
                    break
                ut += dt_h/24.0
            if ut is not None and (t0_ut <= ut < t1_ut):
                outs.append((kind, ut))
    # kind별 중복 제거(시간 반올림 후)
    seen, dedup = set(), []
    for kind, ut in outs:
        key = (kind, round(ut, 6))
        if key not in seen:
            seen.add(key); dedup.append((kind, ut))
    return dedup

def _angle_time_star_near(jd_guess, lon_deg, lat_deg, star_name_with_or_leading_comma, kind, max_iter=8):
    if swe is None:
        raise RuntimeError("Swiss Ephemeris가 필요합니다.")
    phi = lat_deg*DEG
    best_ut, best_abs = None, 1e99
    for dd in (-1, 0, +1):
        jd0 = math.floor(jd_guess) + dd
        ra, dec = _ra_dec_star_deg_ut(jd0 + 0.5, star_name_with_or_leading_comma)
        alpha_h = ra/15.0; dec_r = dec*DEG
        lst_tgt = _lst_target_for_kind(alpha_h, dec_r, phi, kind)
        if lst_tgt is None: 
            continue
        ut = jd0 + (((lst_tgt - _lst(jd0, lon_deg)) % 24.0) / SID_RATE) / 24.0
        for _ in range(max_iter):
            ra, dec = _ra_dec_star_deg_ut(ut, star_name_with_or_leading_comma)
            alpha_h = ra/15.0; dec_r = dec*DEG
            lst_tgt = _lst_target_for_kind(alpha_h, dec_r, phi, kind)
            if lst_tgt is None:
                ut = None; break
            lst_now = _lst(ut, lon_deg)
            dt_h = ((lst_tgt - lst_now) % 24.0) / SID_RATE
            if abs(dt_h) < (0.25/60.0):
                break
            ut += dt_h/24.0
        if ut is None:
            continue
        dabs = abs(ut - jd_guess)
        if dabs < best_abs:
            best_ut, best_abs = ut, dabs
    return best_ut

def _rise_times_planet_in(lon_deg, lat_deg, ipl, t0_ut, t1_ut,
                          alt_m=0.0, P_hPa=1013.25, T_C=10.0):
    """구간 [t0, t1) 내 행성의 기하학적 상승(UT 리스트, h=0°)"""
    phi = lat_deg*DEG
    h0 = 0.0
    outs = []
    jd_days = range(int(math.floor(t0_ut)) - 1, int(math.floor(t1_ut)) + 2)
    for jd0 in jd_days:
        # 정오 기준 초기치
        ra, dec = _ra_dec_planet_deg_ut(jd0 + 0.5, ipl, lon_deg, lat_deg, alt_m)
        dec_r = dec*DEG
        denom = math.cos(phi)*math.cos(dec_r)
        if abs(denom) < 1e-12:
            continue
        cosH0 = (-math.sin(phi)*math.sin(dec_r)) / denom
        if not (-1.0 <= cosH0 <= 1.0):
            continue
        H0_deg = _acos_clip(cosH0)/DEG
        alpha_h = ra/15.0
        lst_target = _norm24(alpha_h - H0_deg/15.0)

        # 고정점 반복
        ut = jd0 + (((lst_target - _lst(jd0, lon_deg)) % 24.0) / SID_RATE) / 24.0
        for _ in range(6):
            ra, dec = _ra_dec_planet_deg_ut(ut, ipl, lon_deg, lat_deg, alt_m)
            dec_r = dec*DEG
            denom = math.cos(phi)*math.cos(dec_r)
            if abs(denom) < 1e-12:
                ut = None; break
            cosH0 = (-math.sin(phi)*math.sin(dec_r)) / denom
            if not (-1.0 <= cosH0 <= 1.0):
                ut = None; break
            H0_deg = _acos_clip(cosH0)/DEG
            alpha_h = ra/15.0
            lst_target = _norm24(alpha_h - H0_deg/15.0)
            lst_now = _lst(ut, lon_deg)
            dt_h = ((lst_target - lst_now) % 24.0) / SID_RATE
            if abs(dt_h) < (0.25/60.0):
                break
            ut += dt_h/24.0
        if ut is not None and (t0_ut <= ut < t1_ut):
            outs.append(ut)
    outs = sorted(set([round(u, 6) for u in outs]))
    return outs

def _sunrise_span_for_local_day(Y, M, D, tz_hours, lon_deg, lat_deg, alt_m=0.0, gregflag=astrology.SE_GREG_CAL):

    """현지 달력일의 '기하학적' 일출→다음 일출 구간(UT, h=0°; 굴절/반지름 무시)"""
    if swe is None:
        raise RuntimeError("Swiss Ephemeris가 필요합니다.")
    jd_local0_ut = swe.swe_julday(Y, M, D, 0.0, gregflag) - tz_hours/24.0
    cands = []
    phi = lat_deg*DEG
    h0 = 0.0

    def _sunrise_near(jd0):
        ra, dec = _ra_dec_planet_deg_ut(jd0 + 0.5, astrology.SE_SUN, lon_deg, lat_deg, alt_m)
        dec_r = dec*DEG
        denom = math.cos(phi)*math.cos(dec_r)
        if abs(denom) < 1e-12:
            return None
        cosH0 = (-math.sin(phi)*math.sin(dec_r)) / denom
        if not (-1.0 <= cosH0 <= 1.0):
            return None
        H0_deg = _acos_clip(cosH0)/DEG
        alpha_h = ra/15.0
        lst_target = _norm24(alpha_h - H0_deg/15.0)
        ut = jd0 + (((lst_target - _lst(jd0, lon_deg)) % 24.0) / SID_RATE)/24.0
        for _ in range(6):
            ra, dec = _ra_dec_planet_deg_ut(ut, astrology.SE_SUN, lon_deg, lat_deg, alt_m)
            dec_r = dec*DEG
            denom = math.cos(phi)*math.cos(dec_r)
            if abs(denom) < 1e-12: return None
            cosH0 = (-math.sin(phi)*math.sin(dec_r)) / denom
            if not (-1.0 <= cosH0 <= 1.0): return None
            H0_deg = _acos_clip(cosH0)/DEG
            alpha_h = ra/15.0
            lst_target = _norm24(alpha_h - H0_deg/15.0)
            lst_now = _lst(ut, lon_deg)
            dt_h = ((lst_target - lst_now) % 24.0) / SID_RATE
            if abs(dt_h) < (0.25/60.0): break
            ut += dt_h/24.0
        return ut

    for k in (-1, 0, +1, +2):
        ut = _sunrise_near(jd_local0_ut + k)
        if ut and (jd_local0_ut <= ut < jd_local0_ut + 1.0):
            cands.append(ut)
    if not cands:
        return None, None
    first = min(cands)

    next_cands = []
    for k in (0, +1, +2, +3):
        ut = _sunrise_near(math.floor(first) + k)
        if ut and ut > first + 1e-8:
            next_cands.append(ut)
    second = min(next_cands) if next_cands else None
    return first, second

# ====== 후보 항성 목록 가져오기 ======
def _get_fixstar_names_for_parans(options):
    """
    유저가 켠 항성만 반환. Swiss 고유 ID 포맷은 ',<code>' 이므로
    모두 콤마를 붙여 돌려준다. (예: 'alLeo' -> ',alLeo')
    """
    try:
        fs = getattr(options, 'fixstars', {})  # dict: {code: orb, ...}
        names = []
        # 파이썬2/3 호환
        try:
            keys_iter = fs.iterkeys()
        except AttributeError:
            keys_iter = fs.keys()
        for k in keys_iter:
            k = (u'' + k)  # ensure unicode on py2
            if not k.startswith(u','):
                k = u',' + k
            names.append(k)
        return names
    except Exception:
        return []

_PLANET_LABEL = {
    astrology.SE_SUN: u"Sun", astrology.SE_MOON: u"Moon", astrology.SE_MERCURY: u"Mercury",
    astrology.SE_VENUS: u"Venus", astrology.SE_MARS: u"Mars", astrology.SE_JUPITER: u"Jupiter",
    astrology.SE_SATURN: u"Saturn"
}
def _extract_local_ymd_tz(self):
    """
    출생 '현지 달력일'(origyear/month/day)과 시간대, 위치를
    차트(self.horoscope)에서 직접 추출한다.
    - tz_hours: (zh + zm/60) * (+1 if plus else -1)
    - 경도/위도: 도+분/60+초/3600, 동(E)/북(N) 양수, 서/남 음수
    """
    h = getattr(self, "horoscope", None)
    if h is None or getattr(h, "time", None) is None or getattr(h, "place", None) is None:
        raise RuntimeError(u"차트의 시간/장소 정보를 찾을 수 없습니다.")

    t = h.time
    p = h.place

    # 1) 현지 달력일 (사용자가 입력한 원래 날짜)
    Y = int(getattr(t, "origyear"))
    M = int(getattr(t, "origmonth"))
    D = int(getattr(t, "origday"))

    # 2) 시간대(시간 단위, +동경/−서경과 무관)
    zh = float(getattr(t, "zh", 0))
    zm = float(getattr(t, "zm", 0))
    plus = bool(getattr(t, "plus", True))
    tz = (zh + zm/60.0) * (1.0 if plus else -1.0)
    # chart.Time.daylightsaving 반영(+1h)
    if bool(getattr(t, "daylightsaving", False)):
        tz += 1.0

    dst_h = float(getattr(t, "dzh", getattr(t, "dsth", 0.0)))
    dst_m = float(getattr(t, "dzm", getattr(t, "dstm", 0.0)))
    dst_flag = bool(getattr(t, "dst", False))
    if dst_flag:
        tz += (dst_h + dst_m/60.0) or 1.0

    # 3) 위치(십진도)
    lon = float(p.deglon) + float(p.minlon)/60.0 + float(getattr(p, "seclon", 0.0))/3600.0
    east = getattr(p, "east", True)
    if isinstance(east, str):
        east_bool = east.strip().upper() in ("E", "+", "EAST", "TRUE", "T", "1")
    else:
        east_bool = bool(east)
    if not east_bool:
        lon = -lon

    lat = float(p.deglat) + float(p.minlat)/60.0 + float(getattr(p, "seclat", 0.0))/3600.0
    north = getattr(p, "north", True)
    if isinstance(north, str):
        north_bool = north.strip().upper() in ("N", "+", "NORTH", "TRUE", "T", "1")
    else:
        north_bool = bool(north)
    if not north_bool:
        lat = -lat

    alt = float(getattr(p, "altitude", 0.0))

    return (Y, M, D, tz, lon, lat, alt)

# ====== UI Wnd ======
class ParanatellontaWnd(cw.CommonWnd):
    """
    Δt | Planet(glyph) | Star Name | Angles  네 칼럼의 커스텀 드로잉 테이블
    - 헤더 아래 구분선
    - Planet은 모리누스 심볼 폰트 사용(이모지/유니코드 아님)
    """

    def __init__(self, parent, horoscope, options, mainfr=None, id=-1, size=wx.DefaultSize):
        self.horoscope = horoscope
        self.options = options
        self.mainfr = mainfr
        self.bw = bool(getattr(self.options, 'bw', False))

        import common

        # FixStarsWnd 규격
        self.FONT_SIZE = int(21*self.options.tablesize)   # 테이블 전체 스케일
        self.SPACE     = self.FONT_SIZE/2                 # 위/아래 여백
        self.LINE_H    = (self.SPACE + self.FONT_SIZE + self.SPACE)   # 행 높이
        self.HEAD_H    = self.LINE_H
        self.SPACE_TITLEY = 0

        # 칼럼 폭 (FixStarsWnd 비율): 작은 셀=3f, 큰 셀=10f, 일반 셀=8f
        self.SMALL_W = 3*self.FONT_SIZE
        self.BIG_W   = 10*self.FONT_SIZE
        self.CELL_W0 = 8*self.FONT_SIZE
        # Δt(작은), Planet(작은), Star(큰), Angles(보통)
        self.COL_W = (self.SMALL_W, self.SMALL_W, self.BIG_W, self.CELL_W0)

        # CommonWnd의 BORDER를 그대로 사용 (상하좌우 여백 통일)
        self.PAD = cw.CommonWnd.BORDER

        # 제목/표 전체 폭
        self.TITLE_W = sum(self.COL_W)

        # 글꼴: FixStarsWnd와 동일(abc / symbols)
        self.f_text = ImageFont.truetype(common.common.abc,      self.FONT_SIZE)
        self.f_sym  = ImageFont.truetype(common.common.symbols,  self.FONT_SIZE)
        try:
            self.f_text_bold = ImageFont.truetype(common.common.abc_bold, self.FONT_SIZE)
        except Exception:
            self.f_text_bold = None

        # 행성/별자리 기호 테이블
        self.signs  = _load_sign_glyphs()
        self.pglyph = _load_planet_glyphs()

        # 칼럼 폭(Planet 좁게, 나머지 균등)
        self.W_DT   = int(5.5 * self.FONT_SIZE)
        self.W_BODY = int(5.5 * self.FONT_SIZE)
        even        = int(10.0 * self.FONT_SIZE)
        self.COL_W  = (self.W_DT, self.W_BODY, even, even)
        self.LINE_H = int(1.85 * self.FONT_SIZE)
        self.HEAD_H = int(2.2  * self.FONT_SIZE)
        self.PAD    = int(0.9  * self.FONT_SIZE)
        # 표 총 폭(컬럼 폭 합계)
        self.TITLE_W = sum(self.COL_W)

        # CommonWnd 초기화 — 이 빌드의 정식 시그니처: (parent, chart, options, id, size)
        cw.CommonWnd.__init__(self, parent, self.horoscope, self.options, id, size)
        # --- 이미지 저장 폴더 보장 ---
        try:
            imgdir = getattr(self.options, 'fpathimgs', None)
            if not imgdir:
                try:
                    base = util.getDocDir()
                except Exception:
                    base = os.getcwd()
                imgdir = os.path.join(base, u"images")
            if not os.path.isdir(imgdir):
                os.makedirs(imgdir)
            if self.mainfr is not None and not hasattr(self.mainfr, 'fpathimgs'):
                self.mainfr.fpathimgs = imgdir
        except Exception:
            pass

        # 데이터 구성 → 배경 그리기
        self.rows = self._compute_rows()
        self.refreshBkg()
    def _planet_rgb(self, ipl):
        """사용자 색상(Colors → Use individual colors) 우선, 없으면 폴백."""
        if getattr(self, 'bw', False):
            return self.clTxt

        # Sun..Pluto 인덱스
        mp = {
            astrology.SE_SUN:0, astrology.SE_MOON:1, astrology.SE_MERCURY:2, astrology.SE_VENUS:3, astrology.SE_MARS:4,
            astrology.SE_JUPITER:5, astrology.SE_SATURN:6, astrology.SE_URANUS:7, astrology.SE_NEPTUNE:8, astrology.SE_PLUTO:9
        }
        idx = mp.get(ipl, 0)

        # 1) Morinus 표준: 개별행성색
        if getattr(self.options, 'useplanetcolors', False) and hasattr(self.options, 'clrindividual'):
            pal = self.options.clrindividual
            try:
                return tuple(pal[idx])
            except Exception:
                pass

        # 2) (있다면) 예전 팔레트 호환
        pal = getattr(self.options, 'clrplanets', None)
        if pal is None:
            try:
                import common
                pal = getattr(common.common, 'clrplanets', None)
            except Exception:
                pal = None
        if isinstance(pal, (list, tuple)):
            try:
                return tuple(pal[idx])
            except Exception:
                pass

        # 3) 최후: 텍스트색
        return self.clTxt

    # --- CommonWnd 필수 구현 ---
    def getExt(self):
        return u"Paran.bmp"

    def getTitle(self):
        return (u"ΔT", mtexts,txts["Planets"], mtexts,txts["FixedStar"], mtexts,txts["Angles"])
    def refreshBkg(self):
        """
        표 내용을 PIL로 그려 self.buffer(wx.Bitmap)를 만든다.
        - 색상(self.clBkg/clTxt/clTbl)이 없을 경우 기본값 부여
        - wx 버전에 따라 Bitmap 생성 경로를 폴백
        """
        # --- 색상: FixStarsWnd와 동일 규칙 ---
        # bw(True)이면 흑백, 아니면 옵션 색상
        if getattr(self, 'bw', False):
            self.clBkg = (255, 255, 255)
            self.clTxt = (  0,   0,   0)
            self.clTbl = (  0,   0,   0)
        else:
            # options에서 받아오기(없으면 안전 기본값)
            self.clBkg = tuple(getattr(self.options, 'clrbackground', (255,255,255)))
            self.clTxt = tuple(getattr(self.options, 'clrtexts',      (  0,  0,  0)))
            self.clTbl = tuple(getattr(self.options, 'clrtable',      (120,120,120)))

        # wx 배경도 일치
        try:
            self.SetBackgroundColour(self.clBkg)
        except Exception:
            pass

        # --- 캔버스 크기 ---
        nrows = max(1, len(getattr(self, 'rows', []) or []))
        rows = getattr(self, 'rows', []) or []
        nrows = max(1, len(rows))

        TABLE_W = self.TITLE_W
        TABLE_H = self.HEAD_H + self.SPACE_TITLEY + nrows*self.LINE_H

        W = int(self.PAD + TABLE_W + self.PAD)
        H = int(self.PAD + TABLE_H + self.PAD)

        # --- PIL 캔버스에 그리기 ---
        img  = Image.new("RGB", (W, H), self.clBkg)
        draw = ImageDraw.Draw(img)
        self.drawBkg(draw)

        # --- PIL → wx.Bitmap (버전별 폴백) ---
        buf = img.tobytes()
        bmp = None
        try:
            # 1) Phoenix 신형
            bmp = wx.Bitmap.FromBuffer(W, H, buf)
        except Exception:
            try:
                # 2) Classic: ImageFromBuffer → BitmapFromImage
                if hasattr(wx, "ImageFromBuffer"):
                    wx_img = wx.ImageFromBuffer(W, H, buf)
                    bmp = wx.BitmapFromImage(wx_img) if hasattr(wx, "BitmapFromImage") else wx.Bitmap(wx_img)
                else:
                    raise AttributeError
            except Exception:
                try:
                    # 3) 더 구형: SetData(bytearray)
                    wx_img = wx.Image(W, H)
                    wx_img.SetData(bytearray(buf))
                    bmp = wx.BitmapFromImage(wx_img) if hasattr(wx, "BitmapFromImage") else wx.Bitmap(wx_img)
                except Exception:
                    # 4) 최후: BMP 메모리 스트림
                    bio = io.BytesIO()
                    img.save(bio, format="BMP")
                    bio.seek(0)
                    if hasattr(wx, "ImageFromStream"):
                        wx_img = wx.ImageFromStream(bio)
                        bmp = wx.BitmapFromImage(wx_img) if hasattr(wx, "BitmapFromImage") else wx.Bitmap(wx_img)
                    else:
                        # 극히 구형: 임시 파일 경유
                        tmp = os.path.join(os.path.dirname(__file__), "_paran_tmp.bmp")
                        with open(tmp, "wb") as f:
                            f.write(bio.getvalue())
                        wx_img = wx.Image(tmp)
                        bmp = wx.BitmapFromImage(wx_img) if hasattr(wx, "BitmapFromImage") else wx.Bitmap(wx_img)
                        try: os.remove(tmp)
                        except Exception: pass

        self.buffer = bmp

        # 스크롤/가상 크기 & 리프레시
        try: self.SetVirtualSize((W, H))
        except Exception: pass
        try:
            self.Refresh(False)
            self.Update()
        except Exception:
            pass

    def drawBkg(self, draw):
        BOR  = self.PAD
        txt  = self.clTxt
        tbl  = self.clTbl

        # --- 헤더 박스(흰 배경에 테두리) ---
        # FixStarsWnd는 왼쪽에 번호 칼럼 때문에 +SMALL_CELL_WIDTH부터 시작하지만
        # 파란 표는 4칼럼이므로 바로 BOR부터 시작
        draw.rectangle(
            ((BOR, BOR), (BOR + self.TITLE_W, BOR + self.HEAD_H)),
            outline=tbl, fill=self.clBkg
        )

        # --- 헤더 텍스트 ---
        headers = (u"ΔT",mtexts.txts["Planets"], mtexts.txts["FixedStar"], mtexts.txts["Angles"])
        x = BOR
        for i, h in enumerate(headers):
            w = self.COL_W[i]
            tw, th = draw.textsize(h, self.f_text)
            draw.text((x + (w - tw)/2, BOR + (self.HEAD_H - th)/2), h, fill=txt, font=self.f_text)
            x += w

        # --- 헤더 아래 굵기 1px 가로선 ---
        y0 = BOR + self.HEAD_H + self.SPACE_TITLEY
        draw.line((BOR, y0, BOR + self.TITLE_W, y0), fill=tbl)

        # --- 본문 행 그리드/텍스트 ---
        rows = getattr(self, 'rows', []) or []
        for r, row in enumerate(rows):
            y = y0 + r*self.LINE_H

            # 아래 가로선
            draw.line((BOR, y + self.LINE_H, BOR + self.TITLE_W, y + self.LINE_H), fill=tbl)

            # 세로선
            x = BOR
            for w in self.COL_W:
                draw.line((x, y, x, y + self.LINE_H), fill=tbl)
                x += w
            # 마지막 오른쪽 테두리
            draw.line((BOR + self.TITLE_W, y, BOR + self.TITLE_W, y + self.LINE_H), fill=tbl)

            # 셀 컨텐츠
            # row = (ΔtTxt, ipl, StarName, AnglesTxt[, same])
            if len(row) == 5:
                dtxt, ipl, star, angles, same = row
            else:
                dtxt, ipl, star, angles = row
                same = False

            # 1) Δt (텍스트 폰트)
            x = BOR
            w = self.COL_W[0]
            # Bold 폰트 있으면 그걸로, 없으면 겹쳐 그려서 두껍게
            tw, th = draw.textsize(dtxt, self.f_text_bold or self.f_text)
            px = x + (w - tw)/2
            py = y + (self.LINE_H - th)/2
            if same and not self.f_text_bold:
                draw.text((px,   py), dtxt, fill=txt, font=self.f_text)
                draw.text((px+1, py), dtxt, fill=txt, font=self.f_text)  # 가짜 Bold
            else:
                draw.text((px, py), dtxt, fill=txt, font=(self.f_text_bold if same else self.f_text))
            x += w

            # 2) Planet (심볼 폰트) — 동일 앵글이면 두껍게
            glyph = self._glyph_for(ipl)
            w = self.COL_W[1]
            tw, th = draw.textsize(glyph, self.f_sym)
            px = x + (w - tw)/2
            py = y + (self.LINE_H - th)/2
            pclr = self._planet_rgb(ipl)

            if same:
                # Morinus 심볼 폰트엔 Bold 파일이 없으므로 겹쳐 그려 '가짜 Bold'
                draw.text((px,   py), glyph, fill=pclr, font=self.f_sym)
                draw.text((px+1, py), glyph, fill=pclr, font=self.f_sym)
            else:
                draw.text((px, py), glyph, fill=pclr, font=self.f_sym)

            x += w

            # 3) Star Name (텍스트 폰트)
            w = self.COL_W[2]
            tw, th = draw.textsize(star, self.f_text_bold or self.f_text)
            px = x + (w - tw)/2
            py = y + (self.LINE_H - th)/2
            if same and not self.f_text_bold:
                draw.text((px,   py), star, fill=txt, font=self.f_text)
                draw.text((px+1, py), star, fill=txt, font=self.f_text)
            else:
                draw.text((px, py), star, fill=txt, font=(self.f_text_bold if same else self.f_text))
            x += w

            # 4) Angles (텍스트 폰트)
            w = self.COL_W[3]
            tw, th = draw.textsize(angles, self.f_text_bold or self.f_text)
            px = x + (w - tw)/2
            py = y + (self.LINE_H - th)/2
            ang_clr = txt
            if same and not self.f_text_bold:
                draw.text((px,   py), angles, fill=ang_clr, font=self.f_text)
                draw.text((px+1, py), angles, fill=ang_clr, font=self.f_text)
            else:
                draw.text((px, py), angles, fill=ang_clr, font=(self.f_text_bold if same else self.f_text))

    # --- 내부: 데이터 산출 (기존 로직 재사용 + Planet을 '라벨'→'ipl 코드'로) ---
    def _compute_rows(self):
        # 원래 클래스의 _compute_rows 로직을 거의 그대로 복사·사용하되,
        # rows.append에서 planet_label 대신 ipl(정수 코드)을 넣는다.
        Y, M, D, tz, lon, lat, alt = _extract_local_ymd_tz(self)
        # chart.Time.cal: 0=GREGORIAN, 1=JULIAN
        t = getattr(self.horoscope, "time", None)
        cal = int(getattr(t, "cal", 0)) if t is not None else 0
        gregflag = astrology.SE_GREG_CAL if cal == 0 else astrology.SE_JUL_CAL
        sr_today, sr_next = _sunrise_span_for_local_day(Y, M, D, tz, lon, lat, alt, gregflag)
        jd_today_ut = swe.swe_julday(Y, M, D, 0.0, gregflag)
        Yp, Mp, Dp, _ = swe.swe_revjul(jd_today_ut - 1.0, gregflag)
        sr_prev, sr_today_again = _sunrise_span_for_local_day(Yp, Mp, Dp, tz, lon, lat, alt, gregflag)

        tobj = getattr(self.horoscope, "time", None)
        jd_ut = getattr(tobj, "jd", None) or getattr(self.horoscope, "jd_ut", None)

        if jd_ut is None:
            return []

        if sr_today and sr_next and (sr_today <= jd_ut < sr_next):
            t0, t1 = sr_today, sr_next
        elif sr_prev and sr_today and (sr_prev <= jd_ut < sr_today):
            t0, t1 = sr_prev, sr_today
        else:
            half = 0.5
            t0, t1 = jd_ut - half, jd_ut + half

        _pad = ANGLE_TOL_MIN / 1440.0
        t0_pad, t1_pad = t0 - _pad, t1 + _pad

        planets = [astrology.SE_SUN, astrology.SE_MOON, astrology.SE_MERCURY, astrology.SE_VENUS, astrology.SE_MARS, astrology.SE_JUPITER, astrology.SE_SATURN]

        planet_events = []
        for ipl in planets:
            for kindP, utP in _angle_times_planet_in(lon, lat, ipl, t0_pad, t1_pad, alt):
                planet_events.append((ipl, kindP, utP))
        if not planet_events:
            return []

        fixstars_ids = _get_fixstar_names_for_parans(self.options)
        if not fixstars_ids:
            return []

        rows = []  # (ΔtTxt, ipl, StarDispName, "P - S")
        for ipl, kindP, utP in planet_events:
            for sid in fixstars_ids:
                for kindS in ANGLE_LABELS:
                    utS = _angle_time_star_near(utP, lon, lat, sid, kindS)
                    if utS is None:
                        continue
                    du = utP - utS
                    if abs(du) * 1440.0 > ANGLE_TOL_MIN + 1e-6:
                        continue
                    dtxt = _fmt_deltat_minutes(du)
                    _tr = {'Asc': mtexts.txts['Asc'], 'Dsc': mtexts.txts['Dsc'],
                        'MC': mtexts.txts['MC'],   'IC':  mtexts.txts['IC']}
                    angles_txt = u"%s - %s" % (_tr.get(kindP, kindP), _tr.get(kindS, kindS))
                    star_disp = _star_display_name(sid, utP)
                    same = (kindP == kindS)  # 동일 앵글?
                    rows.append((dtxt, ipl, star_disp, angles_txt, same))

        def _abs_minutes(txt):
            s = txt.replace(u"±", u"").replace(u"″", u"").split(u"′")
            m = int(s[0]); ss = int(s[1])
            return m + ss/60.0
        rows.sort(key=lambda r: _abs_minutes(r[0]))
        return rows

    def _glyph_for(self, ipl):
        # swe 상수 → pglyph 인덱스
        mp = {
            astrology.SE_SUN:0, astrology.SE_MOON:1, astrology.SE_MERCURY:2, astrology.SE_VENUS:3, astrology.SE_MARS:4,
            astrology.SE_JUPITER:5, astrology.SE_SATURN:6, astrology.SE_URANUS:7, astrology.SE_NEPTUNE:8, astrology.SE_PLUTO:9
        }
        idx = mp.get(ipl, 0)
        try:
            return self.pglyph[idx]
        except Exception:
            return u'?'

