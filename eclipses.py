# -*- coding: utf-8 -*-
from __future__ import division
import math
import astrology  # sweastrology 래퍼
import util       # decToDeg 등

SEFLG = astrology.SEFLG_SWIEPH
# --- 스캔 토글 ---
ENABLE_SOLAR_SCAN = True     # 이제 True로 켜도 크래시 없이 동작 (fallback 사용)
USE_GLOB_SOLAR    = False    # swe_sol_eclipse_when_glob()는 pyd 크래시라 비활성화

# 굵게 처리: 개기일식/금환/혼성, 개기월식
SOLAR_BOLD_FLAGS = (
    astrology.SE_ECL_TOTAL | astrology.SE_ECL_ANNULAR | astrology.SE_ECL_ANNULAR_TOTAL
)
LUNAR_BOLD_FLAGS = astrology.SE_ECL_TOTAL


class EclipseEvent(object):
    __slots__ = ("jdut", "is_solar", "retflag", "elon", "elat", "decl",
                 "dodek_deg", "dodek_sign", "dodek_d", "dodek_m", "dodek_s",
                 "saros", "bold")

    def __init__(self):
        self.jdut = 0.0
        self.is_solar = True
        self.retflag = 0
        self.elon = 0.0
        self.elat = 0.0
        self.decl = 0.0
        self.dodek_deg = 0.0
        self.dodek_sign = 0
        self.dodek_d = 0
        self.dodek_m = 0
        self.dodek_s = 0
        self.saros = u'—'
        self.bold = False

# 정밀 양자화/경계 상수
_ARCSEC_360 = 360 * 3600
_ARCSEC_30  = 30  * 3600
_EPS        = 1e-9          # 경계 보정(부동소수 오류 방지용)

def _normalize_deg(x):
    """[0,360)로 정규화. 360.0000…은 0으로 클램프."""
    t = float(x) % 360.0
    if t < 0.0:
        t += 360.0
    # 359°59′59.9996″ 같은 경우 360°로 튀는 걸 0으로 내림
    if t >= 360.0 - 1e-10:
        t = 0.0
    return t

def _q_arcsec(x_deg, full_circle_arcsec=_ARCSEC_360):
    """
    최종 한 번만 반올림: arcsec = floor(x*3600 + 0.5 - EPS)
    그 뒤 모듈러와 캐리로 DMS 분해.
    """
    asec = int(math.floor(x_deg * 3600.0 + 0.5 - _EPS))
    # 360°나 30° 경계에서 0으로 접힘
    if full_circle_arcsec is not None:
        asec %= full_circle_arcsec
    d = asec // 3600
    m = (asec % 3600) // 60
    s = asec % 60
    return d, m, s, asec  # asec도 돌려줌(도데 사인 계산 때 씀)

def _dms(angle_deg):
    """
    경도/황경 등 [0,360)용 DMS. (정규화→단일 양자화→캐리)
    """
    t = _normalize_deg(angle_deg)
    d, m, s, _ = _q_arcsec(t, _ARCSEC_360)
    return d, m, s

def _dms_signed(angle_deg):
    """
    위도/적위처럼 부호 있는 값: 부호는 따로 두고 절댓값만 양자화.
    """
    sign_neg = (angle_deg < 0)
    d, m, s, _ = _q_arcsec(abs(angle_deg), None)  # 부호값에는 360모듈러 없음
    return ('−' if sign_neg else '+'), d, m, s

def _dodek_from_ecliptic(lon_deg):
    """
    도데카테모리온: (사인 내 위치 × 12)을 전체 원에 투영.
    ★ 핵심: 중간에 절대 '라운딩'하지 않고, 맨 마지막에 한 번만 양자화.
    """
    L = _normalize_deg(lon_deg)
    base_sign = int(math.floor((L + 1e-12) / 30.0))  # 경계에서 사인 흔들림 방지
    pos_in_sign = L - base_sign * 30.0               # [0,30)

    # 사인 내 위치 × 12 → 전체 원에 투영 후 [0,360) 정규화
    proj = (pos_in_sign * 12.0)
    Ld_total = _normalize_deg(base_sign * 30.0 + proj)

    # 최종 한 번만 양자화
    # 먼저 '도데 사인'을 결정하고, 그 사인 내부의 도/분/초를 구함
    s2 = int(math.floor((Ld_total + 1e-12) / 30.0)) % 12
    within = Ld_total - s2 * 30.0                    # [0,30)
    d2, m2, s2sec, asec = _q_arcsec(within, _ARCSEC_30)
    # 드물게 30°00′00″으로 양자화될 수 있는데, 위에서 모듈러로 이미 0 처리됨

    return Ld_total, s2, d2, m2, s2sec

def _angnorm180(x):
    x = (x + 180.0) % 360.0
    if x < 0:
        x += 360.0
    return x - 180.0

def _moon_sun_lon(jd):
    mlon, _, _ = _calc3(jd, astrology.SE_MOON, SEFLG)
    slon, _, _ = _calc3(jd, astrology.SE_SUN,  SEFLG)
    return mlon % 360.0, slon % 360.0

def _dlon_m_minus_s(jd):
    mlon, slon = _moon_sun_lon(jd)
    return _angnorm180(mlon - slon)  # 합삭에서 0°

def _find_new_moons(jd_from, jd_to):
    """일 단위로 부호 변화를 잡아 합삭(신월)을 이분법으로 정밀화."""
    t = jd_from - 2.0
    valsafe = _dlon_m_minus_s(t)
    out = []
    MAX_IT = 40
    while t < jd_to + 2.0:
        t2 = t + 1.0
        v2 = _dlon_m_minus_s(t2)
        if valsafe == 0.0 or valsafe * v2 <= 0.0:
            a, b = t, t2
            fa, fb = valsafe, v2
            # bisection
            for _ in range(MAX_IT):
                m = 0.5*(a+b)
                fm = _dlon_m_minus_s(m)
                if abs(fm) < 1e-4 or (b - a) < 1e-5:
                    out.append(m)
                    break
                # 부호가 바뀌는 구간을 유지
                if fa * fm <= 0.0:
                    b, fb = m, fm
                else:
                    a, fa = m, fm
            # 다음 탐색은 이번 신월을 건너뛰고 진행
            t = t2 + 0.5
            valsafe = _dlon_m_minus_s(t)
            continue
        t = t2
        valsafe = v2
    return out

def _utc_tuple_from_jdut(jdut):
    y, m, d, h = astrology.swe_revjul(jdut, astrology.SE_GREG_CAL)
    hh = int(h)
    mm = int((h - hh) * 60.0)
    ss = int(round(((h - hh) * 60.0 - mm) * 60.0))
    if ss == 60:
        ss = 0; mm += 1
    if mm == 60:
        mm = 0; hh += 1
    return y, m, d, hh, mm, ss


def _calc3(jdut, ipl, flags):
    """
    swe_calc_ut → ((retflag), (xx0..xx5), (serr)) 형태를 기본으로 가정하고
    (lon, lat, dist)를 꺼낸다. 다른 변종도 방어.
    """
    r = astrology.swe_calc_ut(jdut, ipl, flags)

    # 표준(이 프로젝트 pyd): ((retflag), (xx[0..5]), (serr))
    if isinstance(r, tuple) and len(r) >= 2 and isinstance(r[1], (list, tuple)):
        xx = r[1]
        lon = float(xx[0]) if len(xx) > 0 else 0.0
        lat = float(xx[1]) if len(xx) > 1 else 0.0
        dist = float(xx[2]) if len(xx) > 2 else 0.0
        return lon, lat, dist

    # 다른 변종(혹시): (xx, something) 또는 (lon,lat,dist,...) 직접값
    if isinstance(r, tuple) and len(r) >= 1 and isinstance(r[0], (list, tuple)):
        xx = r[0]
        lon = float(xx[0]) if len(xx) > 0 else 0.0
        lat = float(xx[1]) if len(xx) > 1 else 0.0
        dist = float(xx[2]) if len(xx) > 2 else 0.0
        return lon, lat, dist

    if isinstance(r, (list, tuple)) and len(r) >= 3 and all(isinstance(v, (int, float)) for v in r[:3]):
        return float(r[0]), float(r[1]), float(r[2])

    return 0.0, 0.0, 0.0


def _moon_geo_ecl_equ(jdut):
    # 황도 경도/위도
    lon, lat, _ = _calc3(jdut, astrology.SE_MOON, SEFLG)
    # 적위
    _ra, decl, _ = _calc3(jdut, astrology.SE_MOON, SEFLG | astrology.SEFLG_EQUATORIAL)
    return lon, lat, decl


def _unify_when_glob_result(res):
    """
    어떤 빌드든 (retflag, tret)을 뽑아낸다.
    - tret 후보: 길이 10 이상인 시각배열, 없으면 첫 번째 수치 시퀀스
    - retflag 후보: 정수 또는 길이 1의 시퀀스
    실패 시 (0, (nan,)) 반환
    """
    import math
    if not isinstance(res, tuple):
        return 0, (float('nan'),)

    tret = None
    rf = None

    # 1) 길이 10+ 인 시퀀스를 우선 tret로
    for item in res:
        if isinstance(item, (list, tuple)) and len(item) >= 10 and all(isinstance(x, (int, float)) for x in item[:10]):
            tret = item
            break

    # 2) 없으면 수치 시퀀스 아무거나
    if tret is None:
        for item in res:
            if isinstance(item, (list, tuple)) and len(item) >= 1 and isinstance(item[0], (int, float)):
                tret = item
                break

    # 3) retflag: 정수 > 길이1 시퀀스 > 길이1 시퀀스의 첫 원소
    for item in res:
        if isinstance(item, (int, float)):
            rf = item
            break
    if rf is None:
        for item in res:
            if isinstance(item, (list, tuple)) and len(item) == 1 and isinstance(item[0], (int, float)):
                rf = item[0]
                break

    if tret is None:
        tret = (float('nan'),)
    return _flag_int(rf), tret

def _flag_int(rf):
    if isinstance(rf, (list, tuple)):
        for v in rf:
            try:
                return int(v)
            except Exception:
                continue
        return 0
    try:
        return int(rf)
    except Exception:
        return 0

def _sol_when_glob(jd):
    # 빌드별 시그니처 차이(3 or 4 args)를 모두 수용
    try:
        res = astrology.swe_sol_eclipse_when_glob(jd, SEFLG, 0, 0)
    except TypeError:
        try:
            res = astrology.swe_sol_eclipse_when_glob(jd, SEFLG, 0)
        except Exception:
            return 0, (float('nan'),)
    except Exception:
        return 0, (float('nan'),)
    return _unify_when_glob_result(res)

def _lun_when(jd):
    try:
        res = astrology.swe_lun_eclipse_when(jd, SEFLG, 0, 0)
    except TypeError:
        try:
            res = astrology.swe_lun_eclipse_when(jd, SEFLG, 0)
        except Exception:
            return 0, (float('nan'),)
    except Exception:
        return 0, (float('nan'),)
    return _unify_when_glob_result(res)
ANY_SOLAR_FLAGS = (astrology.SE_ECL_TOTAL |
                   astrology.SE_ECL_ANNULAR |
                   astrology.SE_ECL_PARTIAL |
                   astrology.SE_ECL_ANNULAR_TOTAL)

def _sol_where_unify(res):
    """swe_sol_eclipse_where 반환을 (retflag:int, attr:list|None)로 통일."""
    rf = None
    attr = None
    if not isinstance(res, tuple):
        return 0, None
    for item in res:
        if isinstance(item, (int, float)) and rf is None:
            rf = int(item)
        elif isinstance(item, (list, tuple)):
            # attr 후보: 수치가 많이 들어있는 배열(보통 길이 10~20)
            if attr is None and len(item) >= 5 and isinstance(item[0], (int, float)):
                attr = item
    return _flag_int(rf), attr
def _sol_where_retflag(t):
    """
    swe_sol_eclipse_where(t, ifl)의 retflag를 어떤 래퍼 변종에서도 int로 안전 추출.
    반환: int retflag (0이면 식 없음)
    """
    try:
        res = astrology.swe_sol_eclipse_where(t, SEFLG)
    except TypeError:
        try:
            res = astrology.swe_sol_eclipse_where(t, SEFLG, )
        except Exception:
            return 0
    except Exception:
        return 0

    if not isinstance(res, tuple):
        return 0

    # retflag 후보: (l) 단일원소 시퀀스 또는 숫자 하나
    for item in res:
        if isinstance(item, (int, float)):
            return int(item)
        if isinstance(item, (list, tuple)) and len(item) == 1 and isinstance(item[0], (int, float)):
            return int(item[0])
    return 0

def _sol_where_try(t):
    """서명 변종(인자수/반환형) 모두 시도해서 안전하게 결과 받기."""
    try:
        res = astrology.swe_sol_eclipse_where(t, SEFLG)
    except TypeError:
        # 일부 빌드는 (t, iflag, serr)로만 받게 포장되어 있을 수도…
        try:
            res = astrology.swe_sol_eclipse_where(t, SEFLG, )
        except Exception:
            return 0, None
    except Exception:
        return 0, None
    return _sol_where_unify(res)
def _classify_solar_from_retflag(rf):
    """전지구 타입 분류와 굵게 여부를 retflag 비트로 결정."""
    if rf & astrology.SE_ECL_TOTAL:
        return u"TOTAL", True, 3
    if rf & astrology.SE_ECL_ANNULAR_TOTAL:
        return u"HYBRID", True, 2
    if rf & astrology.SE_ECL_ANNULAR:
        return u"ANNULAR", True, 1
    if rf & astrology.SE_ECL_PARTIAL:
        return u"PARTIAL", False, 0
    return u"NONE", False, -1
# Lunar 분류(전지구 타입) + 우선순위
def _classify_lunar_from_retflag(rf):
    PEN = getattr(astrology, 'SE_ECL_PENUMBRAL', 0)  # 빌드에 없을 수도 있음
    if rf & getattr(astrology, 'SE_ECL_TOTAL', 0):         return u"TOTAL",   True, 2
    if rf & getattr(astrology, 'SE_ECL_PARTIAL', 0):       return u"PARTIAL", False, 1
    if PEN and (rf & PEN):                                 return u"PENUMBRAL", False, 0
    return u"UNKNOWN", False, -1

# 이벤트 우선순위(중복 제거용)
def _rank_event(ev):
    rf = int(ev.retflag) if not isinstance(ev.retflag, (list, tuple)) else int(ev.retflag[0])
    if ev.is_solar:
        # 개기(3) > 혼성(2) > 금환(1) > 부분(0)
        if rf & astrology.SE_ECL_TOTAL:         return 3
        if rf & astrology.SE_ECL_ANNULAR_TOTAL: return 2
        if rf & astrology.SE_ECL_ANNULAR:       return 1
        if rf & astrology.SE_ECL_PARTIAL:       return 0
        return -1
    else:
        # 개기(2) > 부분(1) > 반영(0)
        if rf & getattr(astrology, 'SE_ECL_TOTAL', 0):   return 2
        if rf & getattr(astrology, 'SE_ECL_PARTIAL', 0): return 1
        if getattr(astrology, 'SE_ECL_PENUMBRAL', 0) and (rf & astrology.SE_ECL_PENUMBRAL): return 0
        return -1

def _moon_lat(jd):
    # 달 황위(지오센터)
    _, lat, _ = _calc3(jd, astrology.SE_MOON, SEFLG)
    return lat

def _refine_min(f, a, b, it=80, tol=1e-5):
    """
    골든섹션 최소화. tol=1e-5d ≈ 0.864초까지 좁힘(각 DMS 1~2″ 수준 안정).
    """
    phi = (math.sqrt(5.0)-1.0)/2.0
    a, b = (a, b) if a <= b else (b, a)
    c = b - phi*(b-a)
    d = a + phi*(b-a)
    fc, fd = f(c), f(d)
    for _ in range(it):
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - phi*(b-a); fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + phi*(b-a); fd = f(d)
        if (b - a) < tol:
            break
    return 0.5*(a+b)

def _refine_solar_time(ta, tb):
    """
    일식: 합삭(Δλ≈0) + 달 황위(|β|) 동시 최소.
    가중치 ↑, tol ↓ 로 1″~2″ 수준까지 맞춤.
    """
    def F(t):
        return 2.0*abs(_dlon_m_minus_s(t)) + 5.0*abs(_moon_lat(t))
    return _refine_min(F, ta, tb, it=100, tol=1e-5)

def _solar_fallback(jd_from, jd_to):
    # ---- Fallback: 합삭 기반 치밀 스캔 + WHERE 비트 판정 ----
    out = []
    tlist = _find_new_moons(jd_from, jd_to)
    for t0 in tlist:
        t_start = t0 - 0.9
        t_end   = t0 + 0.9
        dt      = 0.02

        hits = []   # (t, rf)
        t = t_start
        while t <= t_end + 1e-9:
            rf = _sol_where_retflag(t)
            if rf & ANY_SOLAR_FLAGS:
                hits.append((t, rf))
            t += dt

        if not hits:
            continue

        def _rank(rf):
            if rf & astrology.SE_ECL_TOTAL:         return 3
            if rf & astrology.SE_ECL_ANNULAR_TOTAL: return 2
            if rf & astrology.SE_ECL_ANNULAR:       return 1
            if rf & astrology.SE_ECL_PARTIAL:       return 0
            return -1

        best_rank = max(_rank(rf) for _, rf in hits)
        times = [tt for (tt, rf) in hits if _rank(rf) == best_rank]
        # 구간을 정밀화: 합삭/노드 조건을 동시에 만족시키는 t*
        ta, tb = (times[0], times[-1]) if len(times) >= 2 else (times[0]-0.08, times[0]+0.08)
        best_t = _refine_solar_time(ta, tb)
        # 같은 등급 비트가 실제 켜지는 시각의 retflag를 대표로
        rf_best = 0
        for tt, rf in hits:
            if _rank(rf) == best_rank and abs(tt - best_t) <= 0.05:
                rf_best = rf; break
        if rf_best == 0:
            rf_best = max((rf for (_, rf) in hits if _rank(rf) == best_rank), key=lambda x: x)

        # 신월 검증: 태양-달 경도차가 |≤ 1.5°|일 때만 일식으로 채택
        if abs(_dlon_m_minus_s(best_t)) > 1.5:
            continue

        elon, elat, decl = _moon_geo_ecl_equ(best_t)
        Ld, s2, d2, m2, s2sec = _dodek_from_ecliptic(elon)
        ev = EclipseEvent()
        ev.jdut = best_t
        ev.is_solar = True
        ev.retflag  = rf_best
        ev.elon, ev.elat, ev.decl = elon, elat, decl
        ev.dodek_deg = Ld; ev.dodek_sign = s2
        ev.dodek_d, ev.dodek_m, ev.dodek_s = d2, m2, s2sec
        ev.saros = u'—'
        # bold 여부는 find_eclipses_around()에서 출생시각 기준으로 한 번에 결정
        ev.bold = False
        out.append(ev)
    return out

def _solar(jd_from, jd_to):
    # when_glob을 쓰고 싶을 때만 True로, 아니면 항상 fallback 사용
    if USE_GLOB_SOLAR and hasattr(astrology, 'swe_sol_eclipse_when_glob'):
        # (when_glob 경로를 정말 쓰려면 여기에 기존 when_glob 루프를 두고,
        #  그게 불안하면 그냥 fallback을 호출해도 됩니다)
        return _solar_fallback(jd_from, jd_to)
    else:
        return _solar_fallback(jd_from, jd_to)

def _lunar(jd_from, jd_to):
    out = []
    jd = jd_from - 1e-6
    safe_guard = 0
    call_count = 0
    MAX_CALLS = 400
    while True:
        call_count += 1
        if call_count > MAX_CALLS:
            break

        retflag, tret = _lun_when(jd)
        retflag = _flag_int(retflag)
        if retflag == 0:
            break

        if not tret or len(tret) == 0:
            jd += 5.0
            safe_guard += 1
            if safe_guard > 50: break
            continue

        tmax = float(tret[0])

        # 월식 정밀화: 망(Δλ≈180) + |β| 최소
        def G(t):
            return abs(abs(_dlon_m_minus_s(t)) - 180.0) + 5.0*abs(_moon_lat(t))
        tmax = _refine_min(G, tmax-0.08, tmax+0.08, it=100, tol=1e-5)

        if not math.isfinite(tmax):
            jd += 5.0
            safe_guard += 1
            if safe_guard > 50: break
            continue

        if tmax > jd_to + 1e-9:
            break
        if tmax <= jd + 1e-6:
            jd += 0.5
            safe_guard += 1
            if safe_guard > 3:
                jd += 5.0
                safe_guard = 0
            continue

        if tmax >= jd_from - 1e-9:
            ev = EclipseEvent()
            ev.jdut = tmax
            ev.is_solar = False
            ev.retflag = retflag
            elon, elat, decl = _moon_geo_ecl_equ(tmax)
            ev.elon, ev.elat, ev.decl = elon, elat, decl
            Ld, s2, d2, m2, s2sec = _dodek_from_ecliptic(elon)
            ev.dodek_deg = Ld; ev.dodek_sign = s2
            ev.dodek_d, ev.dodek_m, ev.dodek_s = d2, m2, s2sec
            ev.saros = u'—'
            # bold 여부는 find_eclipses_around()에서 출생시각 기준으로 한 번에 결정
            ev.bold = False
            out.append(ev)

        jd = tmax + 0.01
        safe_guard = 0
    return out


def find_eclipses_around(chart):
    # chart.time을 안전하게 JD로
    y = chart.time.year; m = chart.time.month; d = chart.time.day
    h = chart.time.hour + chart.time.minute/60.0 + chart.time.second/3600.0
    jd0 = astrology.swe_julday(y, m, d, h, _calflag(chart))

    span = 365.0
    jd_from = jd0 - span
    jd_to   = jd0 + span

    sol = []
    lun = []

    # when_glob 유무와 무관하게, 솔라 스캔 토글만 본다
    if ENABLE_SOLAR_SCAN:
        try:
            sol = _solar(jd_from, jd_to) or []
        except Exception:
            sol = []

    try:
        lun = _lunar(jd_from, jd_to) or []
    except Exception:
        lun = []

    allv = []
    allv.extend(sol)
    allv.extend(lun)
    allv.sort(key=lambda e: e.jdut)
    # 중복 제거(같은 종류에서 0.02일(≈29분) 이내면 하나만 남김: 더 ‘강한’ 타입 우선)
    dedup = []
    TH = 0.02
    for ev in allv:
        if dedup and (ev.is_solar == dedup[-1].is_solar) and abs(ev.jdut - dedup[-1].jdut) < TH:
            if _rank_event(ev) > _rank_event(dedup[-1]):
                dedup[-1] = ev
            # 그렇지 않으면 새 이벤트 버림
        else:
            # 직전 이벤트와 타입이 다르고 '같은 날' 수준(24h 이내)이면 일관성 체크
            if dedup and (ev.is_solar != dedup[-1].is_solar) and abs(ev.jdut - dedup[-1].jdut) < 1.0:
                # Solar는 신월(|Δλ|≈0°), Lunar는 망(|Δλ-180°|≈0°)에 더 부합하는 쪽만 남김
                e_new = abs(_dlon_m_minus_s(ev.jdut))
                e_old = abs(_dlon_m_minus_s(dedup[-1].jdut))
                ok_new = (ev.is_solar  and e_new <  2.0) or ((not ev.is_solar)  and abs(e_new-180.0) < 2.0)
                ok_old = (dedup[-1].is_solar and e_old < 2.0) or ((not dedup[-1].is_solar) and abs(e_old-180.0) < 2.0)
                if ok_new and not ok_old:
                    dedup[-1] = ev
                elif ok_new == ok_old:
                    # 둘 다 비슷하면 우선순위 높은 쪽(개기>혼성>금환>부분 / 개기>부분>반영)
                    if _rank_event(ev) > _rank_event(dedup[-1]):
                        dedup[-1] = ev
                # 둘 중 하나만 남기고 종료
            else:
                dedup.append(ev)

    # --- 여기서부터 bold 대상 결정 로직 추가 ---

    # 1) 일단 전부 bold 해제
    for ev in dedup:
        ev.bold = False

    # 2) 메이저 타입 필터: Solar = Total/Hybrid/Annular, Lunar = Total
    def _is_major(ev):
        rf = int(ev.retflag) if not isinstance(ev.retflag, (list, tuple)) else int(ev.retflag[0])
        if ev.is_solar:
            _kind, is_major, _prio = _classify_solar_from_retflag(rf)
            return is_major   # TOTAL / ANNULAR / HYBRID만 True
        else:
            _kind, is_major, _prio = _classify_lunar_from_retflag(rf)
            return is_major   # TOTAL만 True

    majors = [ev for ev in dedup if _is_major(ev)]

    if majors:
        # 출생 시각 jd0 기준으로 직전/직후 메이저 일·월식 선택
        prevs = [ev for ev in majors if ev.jdut <= jd0]
        nexts = [ev for ev in majors if ev.jdut >= jd0]

        prev_ev = max(prevs, key=lambda e: e.jdut) if prevs else None
        next_ev = min(nexts, key=lambda e: e.jdut) if nexts else None

        if prev_ev is not None:
            prev_ev.bold = True
        if next_ev is not None and next_ev is not prev_ev:
            next_ev.bold = True

    return dedup


def _tz_offset_hours(chart):
    """
    chart.time에서 시/분 오프셋(+DST)을 정밀 추출 → 시간대 시차(시간 단위).
    - 지원 필드(존재하는 것만 사용):
      zh, zm  (시, 분) / zoneh, zonemin / tz, zone / utcoff(시간단위)
      dst, ds, daylight, daylightsaving (True면 +1h)
    """
    t = getattr(chart, 'time', None)
    if t is None:
        return 0.0
    # 1) 시/분 분리형
    hours = None; minutes = 0.0
    for hnm in ('zh','zoneh','hours','zone'):
        v = getattr(t, hnm, None)
        if isinstance(v, (int,float)):
            hours = float(v); break
    for mnm in ('zm','zonemin','minutes','min'):
        v = getattr(t, mnm, None)
        if isinstance(v, (int,float)):
            minutes = float(v); break
    # 2) 단일 시간값
    if hours is None:
        for nm in ('tz','utcoff','utcoffset','offset','z'):
            v = getattr(t, nm, None)
            if isinstance(v, (int,float)):
                hours = float(v); minutes = 0.0; break
    if hours is None:
        hours = 0.0
    # 부호는 hours에 이미 들어있다고 가정(서쪽이면 음수)
    off = hours + (minutes/60.0 if hours>=0 else -minutes/60.0)
    # DST 보정(+1h)
    for dnm in ('dst','ds','daylight','daylightsaving','summer'):
        v = getattr(t, dnm, None)
        if isinstance(v, bool) and v:
            off += 1.0
            break
    return off
def _calflag(chart):
    """
    차트의 달력 설정(Time.cal: 0=그레고리, 1=율리우스)을 Swiss Ephemeris 플래그로 변환.
    속성이 없거나 예외면 기본은 그레고리안.
    """
    try:
        cal = int(getattr(chart.time, 'cal', 0))
    except Exception:
        cal = 0
    return astrology.SE_JUL_CAL if cal == 1 else astrology.SE_GREG_CAL
def _fmt_civil_date(y, m, d):
    """
    천문학적 연도(…,-1,0,1,2,…) → 사람 달력(… 2 BC, 1 BC, AD …) 날짜 문자열.
    예) y=-591  → "0592.MM.DD BC"
        y=   1  → "0001.MM.DD"
    """
    yi = int(y)
    if yi <= 0:
        civ = 1 - yi  # 0 → 1 BC, -1 → 2 BC, …
        return u"%04d.%02d.%02d BC" % (civ, m, d)
    return u"%04d.%02d.%02d" % (yi, m, d)

def _fmt_civil_datetime(y, m, d, hh, mm, ss):
    """
    시각 포함 버전. BC엔 접미사 ' BC'를 붙임.
    """
    yi = int(y)
    if yi <= 0:
        civ = 1 - yi
        return u"%04d.%02d.%02d %02d:%02d:%02d BC" % (civ, m, d, hh, mm, ss)
    return u"%04d.%02d.%02d %02d:%02d:%02d" % (yi, m, d, hh, mm, ss)

def utc_string(jdut):
    y, m, d, hh, mm, ss = _utc_tuple_from_jdut(jdut)
    return u"%04d.%02d.%02d %02d:%02d:%02d" % (y, m, d, hh, mm, ss)

def local_string(jdut, chart):
    """
    차트의 현지시간대로 'YYYY.MM.DD HH:MM:SS' 또는 'YYYY.MM.DD HH:MM:SS BC' 반환
    (차트 달력 설정에 맞춰 율/그레 변환)
    """
    off = _tz_offset_hours(chart)
    jd_local = jdut + off/24.0
    y, m, d, h = astrology.swe_revjul(jd_local, _calflag(chart))
    hh = int(h)
    mm = int((h - hh) * 60.0)
    ss = int(round(((h - hh) * 60.0 - mm) * 60.0))
    if ss == 60:
        ss = 0; mm += 1
    if mm == 60:
        mm = 0; hh += 1
    return _fmt_civil_datetime(y, m, d, hh, mm, ss)
    
def local_date_string(jdut, chart):
    """
    현지시간대의 사람 달력 표기('YYYY.MM.DD' 또는 'YYYY.MM.DD BC') 반환
    """
    off = _tz_offset_hours(chart)
    jd_local = jdut + off/24.0
    y, m, d, _ = astrology.swe_revjul(jd_local, _calflag(chart))
    return _fmt_civil_date(y, m, d)

def dms_string(deg):
    d, m, s = util.decToDeg(deg % 360.0)
    return d, m, s
