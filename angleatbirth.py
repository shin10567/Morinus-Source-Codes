# -*- coding: utf-8 -*-
from __future__ import division
import math
import astrology
import chart
import os
import mtexts
import common
import json

# 안전 문자열 변환(내장 unicode 호출 없이)
_U = type(u'')
_B = type('')
# --- Apparent magnitude index from star catalog (prefers sefstars.txt, falls back to fixstars.cat) ---
_MAG_INDEX = None
def _load_fixstar_mags():
    """
    sefstars.txt(우선) 또는 fixstars.cat(폴백)에서 전통명/약칭 -> 겉보기 등급(=mag) 매핑을 만든다.
    우선순위: 모듈/상위/SWEP/Ephem 경로의 sefstars.txt → 동일 경로의 fixstars.cat.
    """
    global _MAG_INDEX
    if _MAG_INDEX is not None:
        return _MAG_INDEX

    mags = {}
    cat_candidates = []
    # 프로젝트 루트 쪽 흔한 위치들도 시도
    try:
        base = os.path.dirname(__file__)
        # --- sefstars.txt 우선 ---
        cat_candidates.append(os.path.join(base, "sefstars.txt"))
        cat_candidates.append(os.path.join(os.path.dirname(base), "sefstars.txt"))
        cat_candidates.append(os.path.join(base, "SWEP", "Ephem", "sefstars.txt"))
        cat_candidates.append(os.path.join(os.path.dirname(base), "SWEP", "Ephem", "sefstars.txt"))
        # --- 레거시 fixstars.cat 폴백 ---
        cat_candidates.append(os.path.join(base, "fixstars.cat"))
        cat_candidates.append(os.path.join(os.path.dirname(base), "fixstars.cat"))
        cat_candidates.append(os.path.join(base, "SWEP", "Ephem", "fixstars.cat"))
        cat_candidates.append(os.path.join(os.path.dirname(base), "SWEP", "Ephem", "fixstars.cat"))
    except Exception:
        pass
    # 현재 작업폴더 기준
    cat_candidates.append("sefstars.txt")
    cat_candidates.append(os.path.join(os.getcwd(), "SWEP", "Ephem", "sefstars.txt"))
    # 레거시 폴백
    cat_candidates.append("fixstars.cat")
    cat_candidates.append(os.path.join(os.getcwd(), "SWEP", "Ephem", "fixstars.cat"))

    for p in cat_candidates:
        try:
            with open(p, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = [s.strip() for s in line.split(",")]
                    # sefstars.txt / fixstars.cat 공통: 13번째 값이 겉보기 등급(Vmag)
                    if len(parts) < 14:
                        continue
                    try:
                        mag = float(parts[13])
                    except Exception:
                        continue
                    # 999.99 등 dummy는 스킵
                    if mag >= 999.0:
                        continue
                    name = utext(parts[0])
                    nom  = utext(parts[1]) if len(parts) > 1 else u""
                    if name:
                        mags[name] = mag
                    if nom and nom not in mags:
                        mags[nom] = mag
            break
        except IOError:
            continue
        except Exception:
            break

    _MAG_INDEX = mags
    return mags

def utext(x):
    try:
        if isinstance(x, _U):
            return x
        elif isinstance(x, _B):
            return x.decode('utf-8', 'ignore')
        else:
            return u"%s" % (x,)
    except Exception:
        return u"%s" % (x,)
def _get_fixstar_mag(nom, name, mag_index=None):
    """
    Swiss Ephemeris swe_fixstar_mag()를 우선 사용하고,
    실패하거나 사용할 수 없는 경우 로컬 카탈로그 인덱스로 폴백한다.
    nom/name: NUL 제거·strip된 유니코드 문자열.
    """
    # Swiss 쿼리용 후보 식별자: 코드(약칭) 우선, 그 뒤 표시명
    ids = []
    for s in (nom, name):
        try:
            s = utext(s).replace(u'\x00', u'').strip()
        except Exception:
            s = u"%s" % (s,)
        if s and s not in ids:
            ids.append(s)

    for sid in ids:
        query = sid
        try:
            ret, st, mag_val, serr = astrology.swe_fixstar_mag(',' + query)
        except Exception:
            mag_val = None

        mag = None
        if mag_val is not None:
            try:
                if isinstance(mag_val, (list, tuple)):
                    raw = mag_val[0] if len(mag_val) > 0 else None
                else:
                    raw = mag_val
                if raw is not None:
                    mag = float(raw)
            except Exception:
                mag = None

        # 고정별 겉보기 등급의 일반적인 범위(-5~+15 정도)만 허용
        if mag is not None and -15.0 < mag < 20.0 and mag < 998.0:
            return mag

    # 2) 폴백: sefstars.txt / fixstars.cat 인덱스
    try:
        if mag_index is None:
            mag_index = _load_fixstar_mags()
        for sid in ids:
            if sid in mag_index:
                mag = mag_index.get(sid)
                if mag is not None and mag < 998.0:
                    return mag
    except Exception:
        pass

    return None

import builtins

DEG = math.pi/180.0
RAD = 180.0/math.pi
def sind(x): return math.sin(x*DEG)
def cosd(x): return math.cos(x*DEG)
def tand(x): return math.tan(x*DEG)
def asind(x): return math.asin(max(-1.0,min(1.0,x)))*RAD
def atan2d(y,x): return math.atan2(y,x)*RAD
def norm180(a): return (a+180.0)%360.0-180.0
def norm360(a): return (a%360.0+360.0)%360.0

# 자오선( LST == target_deg )에 가장 가까운 시각을 뉴턴식으로 근사
SID_RATE_DEG_PER_DAY = 360.98564736629  # LST의 UT에 대한 변화율(대략)

def _nearest_transit_deg(jd0, target_deg, lon_deg, iters=3):
    """jd0 근처에서 LST(jd) == target_deg 의 해를 찾는다."""
    jd = jd0
    for _ in range(iters):
        lst = _lst_deg(jd, lon_deg)                  # [0,360)
        diff = norm180(lst - target_deg)             # [-180,180)
        jd -= diff / SID_RATE_DEG_PER_DAY            # 1차 근사
    return jd

def _lst_deg(jd_ut, lon_deg):
    gmst_h = astrology.swe_sidtime(jd_ut)
    return norm360(gmst_h*15.0 + lon_deg)

def _altaz_from_radec(ra_deg, dec_deg, jd_ut, lat_deg, lon_deg):
    lst = _lst_deg(jd_ut, lon_deg)
    H = norm180(lst - ra_deg)
    sd, cd = sind(dec_deg), cosd(dec_deg)
    sp, cp = sind(lat_deg), cosd(lat_deg)
    ch, sh = cosd(H), sind(H)
    sin_h = sp*sd + cp*cd*ch
    h  = asind(sin_h)
    y = -cd*sh
    x = sd*cp - cd*sp*ch
    A  = norm360(atan2d(y, x))
    return h, A, H

def _is_south_az(az_deg):
    """남쪽(자오선 남쪽)인가? 90°<Az<270° 면 남쪽."""
    return abs(norm180(az_deg)) > 90.0

def _label_meridian_by_az(az_deg):
    """Az 기준 라벨: 남쪽=MC, 북쪽=IC"""
    return "MC" if _is_south_az(az_deg) else "IC"
    
def _bisect_time(f, t1, t2, tol_sec=0.5, max_iter=50):
    v1, v2 = f(t1), f(t2)
    if v1 == 0: return t1
    if v2 == 0: return t2
    if v1*v2 > 0: return None
    for _ in range(max_iter):
        tm = (t1+t2)/2.0
        vm = f(tm)
        if abs(vm) < 1e-6 or (t2-t1)*86400.0 < tol_sec:
            return tm
        if v1*vm <= 0:
            t2, v2 = tm, vm
        else:
            t1, v1 = tm, vm
    return (t1+t2)/2.0

def _eps_deg(jd_ut):
    T = (jd_ut - 2451545.0)/36525.0
    return 23.439291111 - (46.8150/3600.0)*T - (0.00059/3600.0)*T*T + (0.001813/3600.0)*T*T*T

def _tofloat(x):
    try:
        if isinstance(x, basestring): x = x.replace('\x00','').strip()
        return float(x)
    except: return None

def _radec_from_row(row, jd_ut):
    """
    row: [name, nomname, λ, β, RA, Dec, ...] 형태 가정
    - RA/Dec가 있으면 단위(시간/라디안/도)를 판별해 '도'로 통일
    - 없으면 (λ,β)와 ε로 (RA,Dec) 변환
    """
    def _f(x):
        try:
            if isinstance(x, basestring):
                x = x.replace('\x00', '').strip()
            return float(x)
        except:
            return None

    # 1) RA/Dec 우선 사용
    # Morinus FixStars(FixStars.RA/DECL)는 swe_cotrans 결과로 '도(deg)' 단위임.
    # 여기서 hour/rad 자동변환을 해버리면 RA가 0~24도인 항성들이 오검출/누락된다.
    ra  = row[4]
    dec = row[5]
    if ra is not None and dec is not None:
        try:
            ra  = float(utext(ra).replace(u'\x00', u'').strip())
            dec = float(utext(dec).replace(u'\x00', u'').strip())
        except Exception:
            return None, None
        return norm360(ra), dec

    # 2) 없으면 (λ,β) → (RA,Dec)
    lam = row[2]
    bet = row[3]
    if lam is None or bet is None:
        return None, None

    eps = _eps_deg(jd_ut)
    sin_dec = sind(bet)*cosd(eps) + cosd(bet)*sind(eps)*sind(lam)
    dec = asind(sin_dec)
    y = sind(lam)*cosd(eps) - tand(bet)*sind(eps)
    x = cosd(lam)
    ra = norm360(atan2d(y, x))
    return ra, dec

def _fmt_time_chart_local(ch, jd_ut):
    """
    차트의 시간체계(ZONE / GREENWICH / LOCALMEAN / LOCALAPPARENT)와 DST를 반영해
    'HH.MM.SS' 로 표기.
    - ZONE:         표준 타임존(동/서 표기) + DST
    - GREENWICH:    UT 그대로
    - LOCALMEAN:    경도 기반 오프셋(동경 +, 서경 −) + DST
    - LOCALAPPARENT: LMT − EoT(방정시) + DST
    """
    calflag = astrology.SE_GREG_CAL if ch.time.cal == ch.time.GREGORIAN else astrology.SE_JUL_CAL

    # 기본 오프셋(일 단위)
    off_days = 0.0
    zt = ch.time.zt

    if zt == chart.Time.GREENWICH:
        off_days = 0.0

    elif zt == chart.Time.ZONE:
        ztime_h = float(getattr(ch.time, 'zh', 0.0) or 0.0) + float(getattr(ch.time, 'zm', 0.0) or 0.0)/60.0
        off_days = ( ztime_h if getattr(ch.time, 'plus', False) else -ztime_h ) / 24.0

    elif zt == chart.Time.LOCALMEAN:  # LMT
        long_min = (ch.place.deglon + ch.place.minlon/60.0) * 4.0  # 분
        hours = long_min / 60.0
        off_days = (hours if ch.place.east else -hours) / 24.0

    elif zt == chart.Time.LOCALAPPARENT:  # LAT
        long_min = (ch.place.deglon + ch.place.minlon/60.0) * 4.0
        hours = long_min / 60.0
        lmt_days = (hours if ch.place.east else -hours) / 24.0
        # 방정시(EoT): Morinus 내부 변환을 역으로 적용 → LMT - te
        te_days = 0.0
        try:
            serr, te = astrology.swe_time_equ(jd_ut)
            te_days = te
            if abs(te_days) > 0.5:  # 혹시 분 단위로 오는 빌드 방어
                te_days = te / 1440.0
        except:
            te_days = 0.0
        off_days = lmt_days - te_days

    # DST 되돌리기(입력 시 빼던 1h를 표시 시 더함)
    if getattr(ch.time, 'daylightsaving', False):
        off_days += 1.0 / 24.0

    # 최종 포맷(점 구분)
    y, m, d, ut = astrology.swe_revjul(jd_ut + off_days, calflag)
    hh = int(ut)
    mmf = (ut - hh) * 60.0
    mm = int(mmf)
    ss = int(round((mmf - mm) * 60.0))
    if ss == 60: ss = 0; mm += 1
    if mm == 60: mm = 0; hh += 1
    return u"%02d.%02d.%02d" % (hh, mm, ss)

def compute_contacts(horoscope, options, minutes_window=10):
    ch  = horoscope
    jd0 = ch.time.jd
    calflag = astrology.SE_GREG_CAL if ch.time.cal == ch.time.GREGORIAN else astrology.SE_JUL_CAL
    lon, lat = ch.place.lon, ch.place.lat

    selected = None
    try:
        if getattr(options, 'fixstarsSelected', None):
            selected = set(
                utext(nm).replace(u'\x00',u'').strip()
                for nm in options.fixstarsSelected if nm
            )
    except:
        pass
    # 별칭 맵이 비어 있으면 ephepath에서 복구
    try:
        if (not hasattr(options, 'fixstarAliasMap')) or (not isinstance(options.fixstarAliasMap, dict)) or (len(options.fixstarAliasMap) == 0):
            alias_json = os.path.join(common.common.ephepath, 'fixstar_aliases.json')
            if os.path.isfile(alias_json):
                with open(alias_json, 'r') as _f:
                    data = json.load(_f)
                if isinstance(data, dict):
                    options.fixstarAliasMap = data
    except Exception:
        pass

    rows_all = []
    try: rows_all = ch.fixstars.data[:]
    except: rows_all = []

    rows = []
    for row in rows_all:
        if not row: continue
        disp = utext(row[0]).replace(u'\x00',u'').strip()
        # 코드→선호표시명 적용
        try:
            nom_sel = utext(row[1]).replace(u'\x00',u'').strip() if len(row) > 1 else u""
            if hasattr(options, 'fixstarAliasMap') and isinstance(options.fixstarAliasMap, dict):
                if nom_sel in options.fixstarAliasMap:
                    disp = options.fixstarAliasMap[nom_sel]
        except Exception:
            pass

        if (selected is None) or (disp in selected):
            rows.append(row)
    if not rows:     # 필터로 0개가 되면 전체 사용 (시리우스 누락 방지)
        rows = rows_all[:]

    if not rows:
        return []

    # 스캔 범위: ±window에 한 스텝 마진
    span = minutes_window/1440.0
    step = 15.0/86400.0   # 15초 스텝
    t1, t2 = jd0 - span - step, jd0 + span + step

    out = []
    rank = {"MC":0,"IC":1,"Asc":2,"Dsc":3}

    # 고정별 등급: Swiss Ephemeris swe_fixstar_mag를 우선 사용하고, 실패 시 카탈로그 인덱스로 폴백
    mag_index = _load_fixstar_mags()

    for row in rows:
        name_raw = utext(row[0]).replace(u'\x00',u'').strip()
        nom      = utext(row[1]).replace(u'\x00',u'').strip() if len(row) > 1 else u""
        disp     = name_raw

        # 코드→선호표시명 적용(표시 전용, Swiss 검색에는 name_raw/nom 사용)
        try:
            if hasattr(options, 'fixstarAliasMap') and isinstance(options.fixstarAliasMap, dict):
                if nom in options.fixstarAliasMap:
                    disp = options.fixstarAliasMap[nom]
        except Exception:
            pass

        mag = _get_fixstar_mag(nom, name_raw, mag_index)
        mag_str = u"" if (mag is None) else u"{:.2f}".format(mag)

        ra_deg, dec_deg = _radec_from_row(row, jd0)

        if ra_deg is None or dec_deg is None: continue

        # ─ 지평선: h=0
        prev_t = t1
        prev_h, _, _ = _altaz_from_radec(ra_deg, dec_deg, prev_t, lat, lon)
        tt = t1 + step
        while tt <= t2 + 1e-12:
            h, az, _ = _altaz_from_radec(ra_deg, dec_deg, tt, lat, lon)
            if (prev_h==0.0) or (prev_h<0 and h>0) or (prev_h>0 and h<0):
                root = _bisect_time(lambda jd: _altaz_from_radec(ra_deg, dec_deg, jd, lat, lon)[0],
                                    prev_t, tt)
                if root:
                    _, azr, _ = _altaz_from_radec(ra_deg, dec_deg, root, lat, lon)
                    angle = "Asc" if 0.0 <= azr < 180.0 else "Dsc"
                    out.append(dict(star=disp, angle=angle, mag=mag, mag_str=mag_str,
                                    time_str = _fmt_time_chart_local(ch, root),
                                    dt_min=abs(root-jd0)*1440.0))
            prev_t, prev_h = tt, h
            tt += step

        ra180 = norm360(ra_deg + 180.0)

        t_mc = _nearest_transit_deg(jd0,  ra_deg, lon)
        t_ic = _nearest_transit_deg(jd0, ra180,  lon)

        # MC/IC는 남중/북중(Az) 라벨링이 아니라 상중천/하중천(자오선 통과) 기준으로 기록한다.
        # Algol처럼 적위가 큰 항성은 상중천이어도 북쪽으로 자오선 통과할 수 있어,
        # Az로 MC/IC를 나누면 MC 탐지가 누락될 수 있다.
        dmc = abs(t_mc - jd0) * 1440.0
        dic = abs(t_ic - jd0) * 1440.0

        if dmc <= minutes_window + 1e-6:
            out.append(dict(star=disp, angle="MC", mag=mag, mag_str=mag_str,
                            time_str=_fmt_time_chart_local(ch, t_mc),
                            dt_min=dmc))

        if dic <= minutes_window + 1e-6:
            out.append(dict(star=disp, angle="IC", mag=mag, mag_str=mag_str,
                            time_str=_fmt_time_chart_local(ch, t_ic),
                            dt_min=dic))

    out = [r for r in out if r["dt_min"] <= minutes_window + 1e-6]
    out.sort(key=lambda r: (abs(r["dt_min"]), rank.get(r["angle"], 9), r["star"]))
    return out