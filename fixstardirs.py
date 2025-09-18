# -*- coding: utf-8 -*-
import math
import datetime
import swisseph as swe
import os
import houses
import common  # Morinus의 ephe 경로 사용 (common.common.ephepath)
import chart
import fixstars
import primdirs
import common  # Morinus의 ephe 경로 사용 (common.common.ephepath)
#try: swe.set_ephe_path(common.common.ephepath)
#except: pass
def _ensure_swisseph_path():
    # 1) Morinus 설정에서 우선 시도
    cands = []
    try:
        ep = getattr(common.common, 'ephepath', '')
        if ep:
            ep = os.path.expandvars(os.path.expanduser(ep))
            if not os.path.isabs(ep):
                # 모듈 파일 위치 기준으로 절대경로 변환
                base = os.path.abspath(os.path.dirname(__file__))
                ep_abs = os.path.normpath(os.path.join(base, ep))
                cands += [ep_abs]
            cands += [ep, os.path.join(ep, 'SWEP', 'Ephem')]
    except Exception:
        pass
    # 2) 모듈 기준 상대 경로들
    here = os.path.abspath(os.path.dirname(__file__))
    cands += [
        os.path.join(here, 'SWEP', 'Ephem'),
        os.path.join(here, 'Ephem'),
        here,
        os.environ.get('SWEPH_PATH', '')  # 환경변수 지원
    ]
    # 3) 실제 Swiss Ephemeris 바이너리(se*.se1)가 있는 첫 경로로 설정
    for p in cands:
        if not p:
            continue
        p = os.path.normpath(p)
        try:
            if os.path.isdir(p) and any(fn.lower().startswith(('sepl_', 'sef', 'semo', 'sea'))
                                        for fn in os.listdir(p)):
                swe.set_ephe_path(p)
                return
        except Exception:
            continue
    # 여기까지 못 잡았으면 그대로 두되, 이후 호출부에서 다시 시도/에러 노출
    # (raise로 끊고 싶으면 RuntimeError(...)를 던지도록 바꿔도 됨)

# 최초 1회 시도(실패해도 지나가게)
try:
    _ensure_swisseph_path()
except Exception:
    pass

import re

NAIBOD_COEFF = primdirs.PrimDirs.staticData[primdirs.PrimDirs.NAIBOD][3]  # 1.01456164
# [ADD] ---- Primary Directions Key를 따르는 arc→years 변환 헬퍼 ----
DEG = math.pi / 180.0
TROPICAL_YEAR = 365.2421897

def _norm360(x):
    return x % 360.0

def _sun_coord_deg(jd_ut, equatorial=False):
    _ensure_swisseph_path()
    """equatorial=True면 적경(°), False면 황경(°) 반환"""
    flags = swe.FLG_SWIEPH | (swe.FLG_EQUATORIAL if equatorial else 0)
    try:
        vals, _ = swe.calc_ut(jd_ut, swe.SUN, flags)
    except Exception:
        # 파일(ephe) 없으면 내부 알고리즘(MOSEPH)로 재시도 → 파일 불필요
        flags = swe.FLG_MOSEPH | (swe.FLG_EQUATORIAL if equatorial else 0)
        vals, _ = swe.calc_ut(jd_ut, swe.SUN, flags)
    lon = vals[0]
    return _norm360(lon)


def _true_solar_arc_years(horoscope, options, arc_deg, direct):
    """진태양(적경/황경) 동적키: 출생 시점에서 태양 좌표가 arc_deg만큼 변하는 시점까지의 '연수' 반환"""
    equ  = (options.pdkeyd == primdirs.PrimDirs.TRUESOLAREQUATORIALARC)
    jd0  = _birth_jd_ut(horoscope)
    base = _sun_coord_deg(jd0, equ)
    # Direct이거나(+) / Converse에서도 'Use regressive'가 꺼져 있으면(+) 정방으로, 그렇지 않으면 역방(-)
    sign = +1.0 if (direct or not getattr(options, 'useregressive', False)) else -1.0

    # 하루 이동량으로 초기 추정: 적경/황경 각각에 대해 실제 하루차로 계측
    if sign > 0:
        step = _norm360(_sun_coord_deg(jd0 + 1.0, equ) - base)
    else:
        step = _norm360(base - _sun_coord_deg(jd0 - 1.0, equ))
    if step < 1e-6:
        step = 0.985647  # 안전한 기본치(황경 기준 하루 이동량)
    # wrap-around로 2° 근처가 잡히는 드문 케이스 보정(태양은 ~1°/day가 정상)
    if step > 2.0:
        step = 360.0 - step

    t0 = 0.0
    t1 = sign * (arc_deg / step)  # days
    MAX_DAYS = 400.0  # 1년(≈365d)보다 약간 큰 안전 범위
    if abs(t1) > MAX_DAYS:
        t1 = math.copysign(MAX_DAYS, t1)

    def f(t):
        pos = _sun_coord_deg(jd0 + t, equ)
        if sign > 0:
            return _norm360(pos - base) - arc_deg
        else:
            return _norm360(base - pos) - arc_deg

    f0 = f(t0)
    f1 = f(t1)
    for _ in range(8):
        denom = (f1 - f0)
        if abs(denom) < 1e-12:
            # 기울기 소실 → 폭주 방지: 이분법성 수렴으로 전환
            t2 = 0.5 * (t1 + t0)
        else:
            t2 = t1 - f1 * (t1 - t0) / denom

        # 비정상 추정치(무한/NaN/범위초과) 클램프
        if not math.isfinite(t2) or abs(t2) > MAX_DAYS:
            t2 = 0.5 * (t1 + t0)

        t0, f0, t1, f1 = t1, f1, t2, f(t2)
        if abs(t1 - t0) < 1e-6 or abs(f1) < 1e-9:
            break
    return abs(t1)  

def _birthday_solar_arc_years(horoscope, options, arc_deg):
    """생일태양(적경/황경) 동적키: 출생일과 다음날 태양 이동량으로 환산"""
    equ = (options.pdkeyd == primdirs.PrimDirs.BIRTHDAYSOLAREQUATORIALARC)
    jd0 = _birth_jd_ut(horoscope)
    c0 = _sun_coord_deg(jd0, equ)
    c1 = _sun_coord_deg(jd0 + 1.0, equ)
    d = _norm360(c1 - c0)
    return (arc_deg / d) if d != 0.0 else 0.0

def _arc_to_years_from_primary_key(horoscope, options, arc_deg, direct):
    """PrimDirs의 calcTime 로직을 최소 구현(정적키/동적키 모두 지원)"""
    if options.pdkeydyn:
        # 동적 키
        if options.pdkeyd in (primdirs.PrimDirs.TRUESOLAREQUATORIALARC,
                              primdirs.PrimDirs.TRUESOLARECLIPTICALARC):
            return _true_solar_arc_years(horoscope, options, arc_deg, direct)
        else:
            return _birthday_solar_arc_years(horoscope, options, arc_deg)
    else:
        # 정적 키
        if options.pdkeys == primdirs.PrimDirs.CUSTOMER:
            val = (options.pdkeydeg + options.pdkeymin/60.0 + options.pdkeysec/3600.0)  # deg/year
            return (arc_deg / val) if val != 0.0 else 0.0
        else:
            coeff = primdirs.PrimDirs.staticData[options.pdkeys][primdirs.PrimDirs.COEFF]  # years/deg
            return arc_deg * coeff
# [END ADD]

_FIXSTAR_CAT_DB = None
def _adlat(phi_deg, dec_deg):
    """ADlat = asin(tan φ * tan δ). |tanφ·tanδ| > 1 → ASC/DSC 부재."""
    val = math.tan(math.radians(phi_deg)) * math.tan(math.radians(dec_deg))
    if abs(val) > 1.0:
        return None
    return math.degrees(math.asin(val))

def _ramc_pack(horoscope):
    """RAMC, RAIC, AOASC, DODESC (모리누스와 동일 정의)"""
    try:
        ramc = horoscope.houses.ascmc2[houses.Houses.MC][houses.Houses.RA]
    except Exception:
        ramc = _get_ramc0_deg(horoscope)
    raic   = (ramc + 180.0) % 360.0
    aoasc  = (ramc +  90.0) % 360.0
    dodesc = (ramc + 270.0) % 360.0
    return ramc, raic, aoasc, dodesc

def _arc_direct(base_deg, target_deg):
    """직행(D): base→target 으로 전진해야 하는 양(0..360)"""
    return (target_deg - base_deg) % 360.0

def _arc_converse(base_deg, target_deg):
    """역행(C): base←target 으로 후진해야 하는 양(0..360)"""
    return (base_deg - target_deg) % 360.0

def _fixstars_cat_paths():
    # 네가 말한 경로: 작업폴더\SWEP\Ephem 도 같이 스캔
    import os
    paths = []
    try:
        ep = getattr(common.common, 'ephepath', '')
        if ep:
            paths += [os.path.join(ep, 'fixstars.cat'),
                      os.path.join(ep, 'fixedstars.cat'),
                      os.path.join(ep, 'SWEP', 'Ephem', 'fixstars.cat')]
    except Exception:
        pass
    here = os.path.dirname(__file__)
    paths += [os.path.join(here, 'SWEP', 'Ephem', 'fixstars.cat'),
              os.path.join(here, 'fixstars.cat'),
              os.path.join(here, 'fixedstars.cat')]
    # 존재하는 것만
    return [p for p in paths if os.path.isfile(p)]

def _load_fixstars_cat():
    """
    fixstars/fixedstars.cat을 1회 캐시 로드:
      code -> {name, ra_j2000_deg, dec_j2000_deg, pm_ra_sec, pm_dec_arcsec}
    (콤마 구분 포맷 기준. 없으면 0으로 간주)
    """
    global _FIXSTAR_CAT_DB
    if _FIXSTAR_CAT_DB is not None:
        return _FIXSTAR_CAT_DB

    db = {}
    for path in _fixstars_cat_paths():
        try:
            f = open(path, 'r')
            for line in f:
                s = line.strip()
                if not s or s.startswith('#'):
                    continue
                parts = [p.strip() for p in s.split(',')]
                if len(parts) < 9:
                    continue
                name = parts[0]
                code = parts[1].lstrip(',')
                # RA
                try:
                    ra_h = float(parts[3]); ra_m = float(parts[4]); ra_s = float(parts[5])
                    ra_deg = (ra_h + ra_m/60.0 + ra_s/3600.0) * 15.0
                except:
                    continue
                # Dec
                try:
                    dec_d_raw = parts[6]
                    dec_d = abs(float(dec_d_raw))
                    dec_m = float(parts[7]); dec_s = float(parts[8])
                    sign = -1.0 if str(dec_d_raw).strip().startswith('-') else 1.0
                    dec_deg = sign * (dec_d + dec_m/60.0 + dec_s/3600.0)
                except:
                    continue
                pm_ra_sec = 0.0
                pm_dec_arcsec = 0.0
                if len(parts) >= 11:
                    try:
                        pm_ra_sec = float(parts[9])
                        pm_dec_arcsec = float(parts[10])
                    except:
                        pm_ra_sec = 0.0; pm_dec_arcsec = 0.0
                db[code] = {
                    'name': name,
                    'ra_j2000_deg': ra_deg,
                    'dec_j2000_deg': dec_deg,
                    'pm_ra_sec': pm_ra_sec,
                    'pm_dec_arcsec': pm_dec_arcsec
                }
            f.close()
        except Exception:
            continue

    _FIXSTAR_CAT_DB = db
    return _FIXSTAR_CAT_DB

# --- Python 2/3 unicode helpers ---
try:
    unicode  # Py2
except NameError:
    unicode = str
    basestring = (str, )
# --- fixed stars catalog path helper (supports both names) ---
def _fixstars_cat_path():
    base = getattr(common.common, 'ephepath', '')
    p1 = os.path.join(base, 'fixstars.cat')     # Morinus가 기본으로 찾는 이름
    p2 = os.path.join(base, 'fixedstars.cat')   # 배포에 따라 이 이름인 경우도 있음
    if os.path.exists(p1): return p1
    if os.path.exists(p2): return p2
    return None
def _cat_all_names_in_order():
    """
    카탈로그의 '첫 컬럼 이름'을 위에서 아래로 그대로 읽어 반환.
    콤마/세미콜론/공백 포맷 모두 지원.
    """
    path = _fixstars_cat_path()
    if not path:
        return []
    names = []
    f = open(path, "r")
    try:
        for ln in f:
            if not isinstance(ln, unicode):
                try: ln = ln.decode('utf-8', 'ignore')
                except: pass
            s = ln.strip()
            if (not s) or s.startswith("#"):
                continue
            if "," in s:
                nm = s.split(",", 1)[0].strip()
            elif ";" in s:
                nm = s.split(";", 1)[0].strip()
            else:
                nm = s.split()[0].strip()
            if nm:
                names.append(nm if isinstance(nm, unicode) else unicode(nm))
    finally:
        try: f.close()
        except: pass
    return names
def _ra_dec_star_ofdate_from_code(code, jd_ut):
    """
    code(예: 'alTau')로 카탈로그 DB에서 J2000 좌표+고유운동을 얻고,
    of-date로 세차해서 RA/Dec(deg)를 반환.
    """
    db = _load_fixstars_cat()
    if code not in db:
        raise RuntimeError(u"fixstars.cat에 항성 코드가 없습니다: %s" % code)
    ra0 = db[code]['ra_j2000_deg']
    de0 = db[code]['dec_j2000_deg']
    pmra = db[code].get('pm_ra_sec', 0.0)
    pmde = db[code].get('pm_dec_arcsec', 0.0)

    # (이미 네 파일에 있는) 고유운동/세차 유틸 사용
    # 고유운동: 세기→연 환산 반영
    ra1, de1 = _apply_proper_motion_j2000(ra0, de0, jd_ut, pmra, pmde)
    # TT = UT + ΔT
    jd_tt = jd_ut + swe.deltat(jd_ut)
    ra2, de2 = _j2000_to_ofdate(ra1, de1, jd_tt)
    return ra2, de2, db[code].get('name', code)


# ===== B1950(FK4) → J2000(FK5) → of-date(출생시) 변환 유틸 =====
J2000_JD = 2451545.0  # TT
def _apply_proper_motion_j2000(ra_deg, dec_deg, jd_ut, pm_ra_sec_century, pm_dec_arcsec_century):
    """
    ra/dec: J2000 기준(도)
    pm_ra_sec_century: RA 고유운동 [초(시간)/세기]
    pm_dec_arcsec_century: Dec 고유운동 [호초/세기]
    jd_ut: 출생 UTJulianDay
    """
    # J2000 으로부터 경과 '연'
    dt_years = (jd_ut - J2000_JD) / 365.2421897

    # *** 세기 → 연 으로 환산 ***
    # RA: 초(시간)/세기 → (초/연) → 도/연
    pm_ra_sec_year   = float(pm_ra_sec_century) / 100.0
    d_ra_deg_per_yr  = pm_ra_sec_year * (15.0 / 3600.0)   # 1s(time)=15″
    # Dec: 호초/세기 → (호초/연) → 도/연
    pm_dec_arcsec_year = float(pm_dec_arcsec_century) / 100.0
    d_dec_deg_per_yr   = pm_dec_arcsec_year / 3600.0

    ra_new  = (ra_deg  + d_ra_deg_per_yr  * dt_years) % 360.0
    dec_new =  dec_deg + d_dec_deg_per_yr * dt_years
    if   dec_new >  90.0: dec_new =  90.0
    elif dec_new < -90.0: dec_new = -90.0
    return ra_new, dec_new

def _rad(d): return d * (math.pi/180.0)
def _deg(r): return r * (180.0/math.pi)

def _ra_dec_to_vec(ra_deg, dec_deg):
    ra = _rad(ra_deg); dec = _rad(dec_deg)
    cosd = math.cos(dec)
    return [math.cos(ra)*cosd, math.sin(ra)*cosd, math.sin(dec)]

def _vec_to_ra_dec(v):
    x,y,z = v
    rxy = math.hypot(x,y)
    ra = math.atan2(y, x)
    if ra < 0.0: ra += 2.0*math.pi
    dec = math.atan2(z, rxy)
    return _deg(ra), _deg(dec)

def _norm_vec(v):
    x,y,z = v
    n = math.sqrt(x*x+y*y+z*z)
    if n == 0.0: return [0.0,0.0,0.0]
    return [x/n, y/n, z/n]

def _mat_vec(M, v):
    return [
        M[0][0]*v[0] + M[0][1]*v[1] + M[0][2]*v[2],
        M[1][0]*v[0] + M[1][1]*v[1] + M[1][2]*v[2],
        M[2][0]*v[0] + M[2][1]*v[1] + M[2][2]*v[2],
    ]

# FK4(B1950) → FK5(J2000) (Aoki et al. 1983 근사; proper motion 미사용)
_M_FK4_TO_FK5 = [
    [0.9999256782, -0.0111820611, -0.0048579477],
    [0.0111820610,  0.9999374784, -0.0000271765],
    [0.0048579479, -0.0000271474,  0.9999881997],
]
_A_FK4_TO_FK5 = [-1.62557e-6, -0.31919e-6, -0.13843e-6]  # E-terms 보정 상수

def _fk4_b1950_to_fk5_j2000(ra50_deg, dec50_deg):
    r = _ra_dec_to_vec(ra50_deg, dec50_deg)
    # r_J2000 ≈ M*(r_FK4) + A  (정규화)
    rj = _mat_vec(_M_FK4_TO_FK5, r)
    rj = [rj[0] + _A_FK4_TO_FK5[0],
          rj[1] + _A_FK4_TO_FK5[1],
          rj[2] + _A_FK4_TO_FK5[2]]
    rj = _norm_vec(rj)
    return _vec_to_ra_dec(rj)

# IAU 1976 (Lieske 1979) 프리세션: J2000 → of-date (TT)
def _precession_matrix_J2000_to_date(jd_tt):
    t = (jd_tt - J2000_JD) / 36525.0  # Julian centuries from J2000
    # 호(arcsec)
    zeta  = (2306.2181*t + 0.30188*t*t + 0.017998*t*t*t)
    z     = (2306.2181*t + 1.09468*t*t + 0.018203*t*t*t)
    theta = (2004.3109*t - 0.42665*t*t - 0.041833*t*t*t)
    zeta  = _rad(zeta/3600.0); z = _rad(z/3600.0); theta = _rad(theta/3600.0)
    cz, sz = math.cos(z), math.sin(z)
    czeta, szeta = math.cos(zeta), math.sin(zeta)
    cth, sth = math.cos(theta), math.sin(theta)
    # Rz(-z) * Ry(theta) * Rz(-zeta)
    Rz1 = [[ cz,  sz, 0], [-sz,  cz, 0], [0,0,1]]
    Ry  = [[ cth, 0, -sth], [0,1,0], [ sth,0, cth]]
    Rz2 = [[ czeta,  szeta, 0], [-szeta,  czeta, 0], [0,0,1]]
    # multiply: R = Rz1 * Ry * Rz2
    def _mm(A,B):
        return [[A[0][0]*B[0][0]+A[0][1]*B[1][0]+A[0][2]*B[2][0],
                 A[0][0]*B[0][1]+A[0][1]*B[1][1]+A[0][2]*B[2][1],
                 A[0][0]*B[0][2]+A[0][1]*B[1][2]+A[0][2]*B[2][2]],
                [A[1][0]*B[0][0]+A[1][1]*B[1][0]+A[1][2]*B[2][0],
                 A[1][0]*B[0][1]+A[1][1]*B[1][1]+A[1][2]*B[2][1],
                 A[1][0]*B[0][2]+A[1][1]*B[1][2]+A[1][2]*B[2][2]],
                [A[2][0]*B[0][0]+A[2][1]*B[1][0]+A[2][2]*B[2][0],
                 A[2][0]*B[0][1]+A[2][1]*B[1][1]+A[2][2]*B[2][1],
                 A[2][0]*B[0][2]+A[2][1]*B[1][2]+A[2][2]*B[2][2]]]
    return _mm(_mm(Rz1, Ry), Rz2)

def _j2000_to_ofdate(ra2000_deg, dec2000_deg, jd_tt):
    R = _precession_matrix_J2000_to_date(jd_tt)
    v0 = _ra_dec_to_vec(ra2000_deg, dec2000_deg)
    v  = _mat_vec(R, v0)
    v  = _norm_vec(v)
    return _vec_to_ra_dec(v)
    
def _clamp(x, a, b): 
    return a if x < a else b if x > b else x

def _norm360(x):
    x = x % 360.0
    return x if x >= 0 else x + 360.0

def asc_dsc_exists(phi_deg, dec_deg):
    # |tan φ * tan δ| <= 1 이어야 상승/하강 존재
    x = abs(math.tan(phi_deg*DEG) * math.tan(dec_deg*DEG))
    return x <= 1.0 - 1e-12  # 임계 근접 수치 폭주 방지 마진

def _pair_arc_and_label(diff_deg):
    """
    primdirs.create()와 같은 규칙:
      - 작은호(≤180)를 기본으로 취하고, 그때의 레이블이 D(직행)
      - 보완호(360-작은호)는 C(역행)
      - diff가 180초과면 레이블을 뒤집는 효과가 발생
    """
    d = diff_deg % 360.0
    if d <= 180.0:
        return (d, 'D'), (360.0 - d, 'C')
    else:
        # 작은호는 360-d (역행이 더 가깝다)
        return (360.0 - d, 'C'), (d, 'D')

def primary_arcs(ramc0_deg, ramc_evt_deg):
    # Direct/Converse 모두 "미래 나이"로 매핑
    arc_dir  = _norm360(ramc_evt_deg - ramc0_deg)
    arc_conv = _norm360(ramc0_deg - ramc_evt_deg)
    return arc_dir, arc_conv

def arc_to_age_years_naibod(arc_deg):
    return arc_deg / 360.0

def _get_ramc0_deg(horoscope):
    # 1) 이미 계산된 RAMC 보유 시 재사용
    for cand in ("ramc", "RAMC", "ramc_deg", "ramc0"):
        if hasattr(horoscope, cand):
            val = getattr(horoscope, cand)
            try:
                return float(val) % 360.0
            except:
                pass
    # 2) Fallback: LST(그리니치 항성시 + 경도)로 계산
    jd_ut = float(getattr(horoscope, "jd_ut", getattr(horoscope, "jdut", 0.0)))
    lon_deg = float(getattr(horoscope, "lon", getattr(horoscope, "longitude", 0.0)))
    sid_hours = swe.sidtime(jd_ut)  # Greenwich sidereal time [hours]
    lst_deg = (sid_hours * 15.0 + lon_deg) % 360.0
    return lst_deg

def _birth_jd_ut(horoscope):
    try:
        return float(horoscope.time.jd)
    except:
        return float(getattr(horoscope, "jd_ut", getattr(horoscope, "jdut", 0.0)))

def _observer_lat(horoscope):
    try:
        return float(horoscope.place.lat)
    except:
        pass
    try:
        deglat = float(horoscope.place.deglat)
        minlat = float(getattr(horoscope.place, 'minlat', 0.0))
        seclat = float(getattr(horoscope.place, 'seclat', 0.0))
        north  = bool(getattr(horoscope.place, 'north', True))
        lat = abs(deglat) + minlat/60.0 + seclat/3600.0
        if not north:
            lat = -lat
        return lat
    except:
        return float(getattr(horoscope, "lat", getattr(horoscope, "latitude", 0.0)))
def _calendar_flag(chrt, options):
    # 1=Gregorian, 0=Julian
    try:
        calobj = getattr(chrt, "time", None)
        if calobj is not None:
            return 0 if calobj.cal == chart.Time.JULIAN else 1
    except Exception:
        pass
    cal = getattr(options, "calendar", "greg")
    if isinstance(cal, int):
        return 1 if cal != 0 else 0
    cal = str(cal).lower()
    return 1 if ("greg" in cal or cal == "g") else 0
def _cat_name_to_code_map():
    """카탈로그 DB에서 name→code 매핑 생성."""
    db = _load_fixstars_cat()
    m = {}
    for code, rec in db.items():
        nm = rec.get('name', u'')
        if not isinstance(nm, unicode):
            try: nm = unicode(nm)
            except: pass
        m[nm] = code
    return m

def _selected_star_codes(options):
    """
    우선순위:
      1) options.fixstars 가 dict이면 그 'key(코드)'만 사용
      2) options.pdfixstarssel 이 dict이면 True인 '이름'을 code로 매핑해 사용
      (둘 다 없으면 빈 리스트)
    반환: ['alTau', 'spica', ...] 처럼 카탈로그 'code' 리스트
    """
    # 1) fixstars: {code: ...}
    fs = getattr(options, 'fixstars', None)
    if isinstance(fs, dict) and len(fs) > 0:
        try:
            keys_iter = fs.iterkeys()
        except AttributeError:
            keys_iter = fs.keys()
        out = []
        for k in keys_iter:
            ku = k if isinstance(k, unicode) else unicode(k)
            ku = ku.strip().lstrip(',')  # 혹시 앞에 콤마가 붙어 있다면 제거
            if ku:
                out.append(ku)
        if out:
            return out

    # 2) pdfixstarssel: {display name: True/False}
    selmap = getattr(options, 'pdfixstarssel', None)
    if isinstance(selmap, dict) and len(selmap) > 0:
        name2code = _cat_name_to_code_map()
        out = []
        for nm, flag in selmap.items():
            if not flag:
                continue
            nmu = nm if isinstance(nm, unicode) else unicode(nm)
            code = name2code.get(nmu)
            if code:
                out.append(code)
        if out:
            return out

    # 3) 아무 것도 못 찾음
    return []

def _options_selected_stars(options):
    """
    사용자가 켠 항성만 반환.
    반환값: ['alTau', 'alLeo', ...]  # fixstars.cat의 'code' 필드 (콤마 없이)
    (paranwnd.py와 동일한 방식: options.fixstars 딕셔너리의 key만 사용)
    """
    try:
        fs = getattr(options, 'fixstars', {})
    except Exception:
        return []
    # Py2/3 호환 키 이터레이터
    try:
        keys_iter = fs.iterkeys()
    except AttributeError:
        keys_iter = fs.keys()

    out = []
    for k in keys_iter:
        # unicode 보정
        try:
            ku = k if isinstance(k, unicode) else unicode(k)
        except NameError:
            ku = k
        out.append(ku.strip())
    return out

    # 2-2) 딕셔너리 {이름: bool}
    if isinstance(cand, dict):
        return [ (k if isinstance(k, unicode) else unicode(k)) for k, v in cand.items() if bool(v) ]

    # 2-3) 리스트/튜플: (이름,) 또는 (이름, bool) 또는 그냥 이름 문자열
    if isinstance(cand, (list, tuple)):
        out = []
        for it in cand:
            if isinstance(it, (list, tuple)) and len(it) >= 1:
                nm = it[0]
                flag = True if len(it) == 1 else bool(it[1])
                if flag:
                    out.append(nm if isinstance(nm, unicode) else unicode(nm))
            elif isinstance(it, basestring):
                out.append(it if isinstance(it, unicode) else unicode(it))
        return out

    # 2-4) 없거나 인식 실패 → 빈 목록
    return []

    # 3-2) 딕셔너리 {이름: bool}
    if isinstance(cand, dict):
        out = [ (k if isinstance(k, unicode) else unicode(k)) for k,v in cand.items() if v ]
        return out

    # 3-3) 리스트/튜플: (이름,) 또는 (이름, bool) 또는 그냥 이름 문자열들
    if isinstance(cand, (list, tuple)):
        out = []
        for it in cand:
            if isinstance(it, (list, tuple)) and len(it) >= 1:
                nm = it[0]
                flag = True if len(it) == 1 else bool(it[1])
                if flag:
                    out.append(nm if isinstance(nm, unicode) else unicode(nm))
            elif isinstance(it, basestring):
                out.append(it if isinstance(it, unicode) else unicode(it))
        return out

    # 그 외는 지원 안 함 → 빈 목록
    return []

def _fallback_names_from_cat(path=None):
    """
    선택 리스트를 못 얻었을 때 최후의 안전장치.
    Morinus의 ephe 경로에 있는 fixedstars.cat에서 '이름'만 긁어온다.
    라인 포맷이 버전별로 다르므로 세미콜론/탭/다중 공백을 모두 시도.
    """
    if path is None:
        path = _fixstars_cat_path()
    if not path:
        return []

    names = []
    try:
        with open(path, "r") as f:
            for ln in f:
                ln = ln.strip()
                if not ln or ln.startswith("#"):
                    continue
                if ";" in ln:
                    parts = [x.strip() for x in ln.split(";")]
                    nm = parts[0]
                elif "\t" in ln:
                    nm = ln.split("\t", 1)[0].strip()
                else:
                    # 연속 공백 분리
                    toks = ln.split()
                    nm = toks[0]
                if nm:
                    names.append(unicode(nm) if not isinstance(nm, unicode) else nm)
    except Exception:
        pass
    return names

def _star_ofdate_ra_dec(star_name, jd_ut):
    """
    카탈로그(콤마/세미콜론/공백)에서 좌표를 읽고,
    B1950이면 FK4→FK5(J2000) 변환 후 of-date 프리세션,
    J2000/ICRS이면 바로 of-date 프리세션.
    반환: of-date RA[deg], Dec[deg], "Name, mag"
    """
    ra_cat, dec_cat, mag, frame = _cat_lookup_equ_generic(star_name)
    if frame == 'B1950':
        ra2000, dec2000 = _fk4_b1950_to_fk5_j2000(ra_cat, dec_cat)
    else:
        ra2000, dec2000 = ra_cat, dec_cat

    # TT≈UT 가정(전통 PD 해상도엔 충분)
    jd_tt = jd_ut + swe.deltat(jd_ut)
    ra_d, dec_d = _j2000_to_ofdate(ra2000, dec2000, jd_tt)

    info = u"{0}, {1}".format(star_name, u"" if mag is None else u"{0}".format(mag)).strip()
    return ra_d, dec_d, info

def _cat_lookup_equ_generic(star_name, path=None):
    """
    fixstars/fixedstars.cat 의 좌표 파싱 (콤마/세미콜론/공백 포맷 모두 지원).
    반환: (ra_deg, dec_deg, mag, frame)  # frame: 'B1950' 또는 'J2000'
    - 콤마 포맷 예:
      Aldebaran  ,alTau,ICRS,04,35,55.2387,16,30,33.485, ...
      (name, alias, frame, RA_h,RA_m,RA_s, Dec_d,Dec_m,Dec_s, ...)
    - 세미콜론 포맷 예:
      Aldebaran; 04 35 55.24; +16 30 33.5; 0.86
    - 공백/탭 포맷 예:
      Aldebaran 04 35 55.24 +16 30 33.5 0.86
    """
    if path is None:
        path = _fixstars_cat_path()
    if not path:
        raise ValueError("fixed stars catalog not found")

    def hms_to_deg(h, m, s): return (h + m/60.0 + s/3600.0) * 15.0
    def dms_to_deg(sign, d, m, s):
        val = d + m/60.0 + s/3600.0
        return val if sign >= 0 else -val

    want = star_name.strip().lower()

    f = open(path, "r")
    try:
        for ln in f:
            if not isinstance(ln, unicode):
                try: ln = ln.decode('utf-8', 'ignore')
                except: pass
            s = ln.strip()
            if (not s) or s.startswith("#"):
                continue

            name = None; alias = None; ra_tokens = None; dec_tokens = None
            mag = None; frame = 'J2000'  # 기본값(J2000/ICRS 취급)

            if "," in s:
                parts = [x.strip() for x in s.split(",")]
                if len(parts) >= 9:
                    name  = parts[0]
                    alias = parts[1] if len(parts) > 1 else None
                    fr    = parts[2].upper() if len(parts) > 2 else ""
                    if "1950" in fr or "B1950" in fr or "FK4" in fr:
                        frame = 'B1950'
                    else:
                        frame = 'J2000'  # 'ICRS','2000' 등은 전부 J2000 취급
                    ra_tokens  = [parts[3], parts[4], parts[5]]
                    dec_tokens = [parts[6], parts[7], parts[8]]
                    # 뒤쪽 토큰들 중 -2~+7 사이 값(대략 Vmag) 하나를 잡아본다(선택)
                    for tok in parts[9:]:
                        tok = tok.strip()
                        try:
                            v = float(tok)
                            if -2.5 <= v <= 8.5:
                                mag = v
                                break
                        except:
                            pass

            elif ";" in s:
                parts = [x.strip() for x in s.split(";")]
                if len(parts) >= 3:
                    name = parts[0]
                    ra_tokens  = parts[1].replace(":", " ").split()
                    dec_tokens = parts[2].replace(":", " ").split()
                    frame = 'B1950'
                    if len(parts) >= 4:
                        try: mag = float(parts[3].split()[0])
                        except: pass

            else:
                toks = re.split(r"[ \t]+", s)
                if len(toks) >= 7:
                    name = toks[0]
                    ra_tokens  = [toks[1], toks[2], toks[3]]
                    dec_tokens = [toks[4], toks[5], toks[6]]
                    frame = 'B1950'
                    if len(toks) >= 8:
                        try: mag = float(toks[7])
                        except: pass

            if not name or not ra_tokens or not dec_tokens:
                continue

            # 이름/별칭 매칭(대소문자/공백 무시)
            nm = name.strip().lower()
            al = alias.strip().lower() if alias else None
            if want != nm and (al is None or want != al):
                continue

            # 숫자화
            try:
                rh, rm, rs = float(ra_tokens[0]), float(ra_tokens[1]), float(ra_tokens[2])
                dd0 = dec_tokens[0]; sgn = -1 if dd0.startswith("-") else 1
                dd  = float(dd0.replace("+","").replace("-",""))
                dm, ds = float(dec_tokens[1]), float(dec_tokens[2])
            except:
                continue

            ra_deg  = hms_to_deg(rh, rm, rs)
            dec_deg = dms_to_deg(sgn, dd, dm, ds)
            return ra_deg, dec_deg, mag, frame

    finally:
        try: f.close()
        except: pass

    raise ValueError("Star not found in catalog: {0}".format(star_name))

def _date_string_from_jd(jd_ut, chrt, options):
    gregflag = _calendar_flag(chrt, options)  # 1=Greg, 0=Jul
    y, m, d, frac = swe.revjul(jd_ut, gregflag)  # UTC 기준
    hh = int(frac * 24.0)
    mm = int((frac * 24.0 - hh) * 60.0)
    return u"{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d} UTC".format(y, m, d, hh, mm)

def compute_fixedstar_angle_rows(horoscope, options, age_max_years=150.0):
    rows = []

    # 0) 기본 상수
    NAIBOD_DEG_PER_DAY = 360.0 / 365.2421897

    # 1) 출생 RAMC/위도
    ramc0 = _get_ramc0_deg(horoscope)        # 기존 함수 그대로 사용
    phi   = _observer_lat(horoscope)         # 위도 얻기 (이미 정의돼 있음)
    jd0   = getattr(getattr(horoscope, 'time', None), 'jd', None)
    if jd0 is None:
        return []

    # 2) 사용자가 켠 항성 '코드'만 모으기
    codes = _selected_star_codes(options)
    if not codes:
        return []

    # 표시용 이름 가져오기 위해 DB 미리 로드
    _db_cache = _load_fixstars_cat()
    # 3) 각 항성(코드)에 대해 네 각도 계산 → 150년 확장
    max_days = age_max_years * 365.2421897
    for code in codes:
        # of-date RA/Dec 계산(세차+고유운동 반영)
        try:
            ra, dec, dispname = _ra_dec_star_ofdate_from_code(code, jd0)
        except Exception:
            continue
        # 표시용 이름이 DB에 있으면 그걸로 덮어쓰기
        try:
            dispname = _db_cache.get(code, {}).get('name', dispname)
        except Exception:
            pass
        if not isinstance(dispname, unicode):
            try: dispname = unicode(dispname)
            except: pass

        # 출생 RAMC 세트 (MC, IC, AOASC, DODESC)
        ramc, raic, aoasc, dodesc = _ramc_pack(horoscope)

        # ADlat로 ASC/DSC 가능성 판단
        ad = _adlat(phi, dec)

        # 각도쌍: (표시각, target, base)
        pairs = [
            ("MC",  ra,              ramc),
            ("IC",  ra,              raic),
        ]
        if ad is not None:
            aostar = (ra - ad) % 360.0
            dostar = (ra + ad) % 360.0
            pairs += [
                ("ASC", aostar, aoasc ),
                ("DSC", dostar, dodesc),
            ]

        # 정방/역방 각각 1개씩만 생성 (k회전 확장 금지)
        for sig, target, base in pairs:
            arcD = _arc_direct(base, target)    # 0..360
            arcC = _arc_converse(base, target)  # 0..360

            # 이 두 줄을 아래 두 줄로 교체
            yrsD = _arc_to_years_from_primary_key(horoscope, options, arcD, True)
            yrsC = _arc_to_years_from_primary_key(horoscope, options, arcC, False)

            if 0.0 <= yrsD <= age_max_years:
                jd_evt = jd0 + yrsD * 365.2421897
                rows.append({
                    'prom': dispname,
                    'dc'  : 'D',
                    'sig' : sig,
                    'arc' : arcD,
                    'jd'  : jd_evt,
                })

            if 0.0 <= yrsC <= age_max_years:
                jd_evt = jd0 + yrsC * 365.2421897
                rows.append({
                    'prom': dispname,
                    'dc'  : 'C',
                    'sig' : sig,
                    'arc' : arcC,
                    'jd'  : jd_evt,
                })


    # 4) 날짜 오름차순 정렬 후 문자열화
    rows.sort(key=lambda r: r['jd'])
    for r in rows:
        r['date'] = _date_string_from_jd(r['jd'], horoscope, options)

    return rows
