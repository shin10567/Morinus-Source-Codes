
# -*- coding: utf-8 -*-
from __future__ import division
import math, datetime
import astrology
import math
import astrology, chart
from angleatbirth import _fmt_time_chart_local
import mtexts
def jd_to_local_YMD_HM(ch, jd_ut):
    # 차트 달력 플래그 Chart Calendar Flag
    calflag = astrology.SE_GREG_CAL if ch.time.cal == chart.Time.GREGORIAN else astrology.SE_JUL_CAL

    # angleatbirth의 포맷터는 HH.MM.SS만 주니까,
    # 날짜는 swe_revjul(jd_ut + 오프셋)을 써서 얻습니다.
    # → 오프셋 산출 로직은 _fmt_time_chart_local과 동일하게 구현.
    # The formatter for angleatbirth is HH. Just give me MM.SS,
    # The date is obtained by writing swe_revjul(jd_ut + offset).
    # → The offset output logic is implemented in the same way as _fmt_time_chart_local .

    off_days = 0.0
    zt = ch.time.zt
    if zt == chart.Time.ZONE:
        ztime_h = float(getattr(ch.time, 'zh', 0.0) or 0.0) + float(getattr(ch.time, 'zm', 0.0) or 0.0)/60.0
        off_days += (ztime_h if getattr(ch.time, 'plus', False) else -ztime_h) / 24.0
    elif zt == chart.Time.LOCALMEAN:  # LMT
        long_min = (ch.place.deglon + ch.place.minlon/60.0) * 4.0
        hours = long_min / 60.0
        off_days += (hours if ch.place.east else -hours) / 24.0
    elif zt == chart.Time.LOCALAPPARENT:  # LAT
        long_min = (ch.place.deglon + ch.place.minlon/60.0) * 4.0
        hours = long_min / 60.0
        lmt_days = (hours if ch.place.east else -hours) / 24.0
        # 방정시(EoT)
        try:
            ret, te, serr = astrology.swe_time_equ(jd_ut)
            te_days = te if abs(te) <= 0.5 else te/1440.0
        except Exception:
            te_days = 0.0
        off_days += (lmt_days - te_days)
    if getattr(ch.time, 'daylightsaving', False):
        off_days += 1.0/24.0

    # 날짜/시각
    # Date/Time
    y, m, d, ut = astrology.swe_revjul(jd_ut + off_days, calflag)
    hh = int(ut); mm = int((ut - hh)*60.0)

    # 시각 포맷은 기존 함수 재사용(점 표기 유지)
     # Visual format reuses existing functions (keep punctuation)
    #视觉格式重复使用现有函数（保留点标记）
    hhmmss = _fmt_time_chart_local(ch, jd_ut)  # 예: "06.10.00"
    return u"{:04d}-{:02d}-{:02d} {}".format(y, m, d, hhmmss)

# --- exact-output caches (py2 fallback 포함) ---包含
try:
    from functools import lru_cache
except Exception:
    def lru_cache(maxsize=None):
        def deco(fn):
            cache = {}
            def wrapped(*args):
                if args in cache:
                    return cache[args]
                out = fn(*args)
                if maxsize and len(cache) >= maxsize:
                    cache.clear()   # 단순 캐시 리셋(정확도 불변)
                cache[args] = out
                return out
            return wrapped
        return deco
# --- float helper (Py2 safe) ---
def _f(x, default=None):
    try:
        return float(x)
    except Exception:
        return float(0.0 if default is None else default)

# --- coordinate caches (둘 다 필요) --- 两者都需要
@lru_cache(maxsize=262144)
def equ_coords(jd_ut, ipl):
    _, eq, _ = swe_calc_ut_ex(jd_ut, ipl, astrology.SEFLG_SWIEPH + astrology.SEFLG_EQUATORIAL)
    return (eq[0], eq[1], eq[2])  # RA, Dec, Dist

@lru_cache(maxsize=262144)
def ecl_coords(jd_ut, ipl):
    _, ec, _ = swe_calc_ut_ex(jd_ut, ipl, astrology.SEFLG_SWIEPH)
    return (ec[0], ec[1], ec[2])  # λ, β, Dist

# --- alt/az cache (위치·천체·시각 기준) --- 位置、天体、视觉标准
@lru_cache(maxsize=262144)
def altaz_cached(jd_ut, ipl, lon, lat, alt_m):
    a = _alt_eff_geom(alt_m)
    astrology.swe_set_topo(lon, lat, a)
    ra, dec, _ = equ_coords(jd_ut, ipl)
    p_hpa, t_c = _refr_params(REFRACTION_MODE, alt_m)
    xaz = astrology.swe_azalt(float(jd_ut), astrology.SE_EQU2HOR,
                                float(lon), float(lat), float(a),
                                float(p_hpa), float(t_c),
                                float(ra), float(dec), 1.0)
    az, alt = xaz[0], xaz[1]
    return (float(alt), float(az))

_SUN_EVENT_CACHE = {}
@lru_cache(maxsize=262144)
def _calc_ut_cache(jd_ut, ipl, flags):
    rflag, xx, serr = astrology.swe_calc_ut(jd_ut, ipl, flags)
    # 리스트는 캐시에 넣기 불편하니 튜플로 저장
    #列表不方便放入缓存，所以保存为tuple
    return (rflag, (xx[0], xx[1], xx[2]), serr)

def calc_ut(jd_ut, ipl, flags):
    rflag, txx, serr = _calc_ut_cache(jd_ut, ipl, flags)
    # 호출부와 동일한 list 타입으로 돌려준다 (완전 동작 동일)
    #返回与呼叫簿相同的list类型（完全动作相同）
    return rflag, [txx[0], txx[1], txx[2]], serr

@lru_cache(maxsize=131072)
def _pheno_ut_cache(jd_ut, ipl, flags):
    rflag, attr, serr = astrology.swe_pheno_ut(jd_ut, ipl, flags)
    return (rflag, tuple(attr), serr)

def pheno_ut(jd_ut, ipl, flags):
    rflag, tattr, serr = _pheno_ut_cache(jd_ut, ipl, flags)
    return rflag, list(tattr), serr

# HG 위상함수 기반 근태양 보정 (연속, 하드컷 없음)
#HG基于相位函数的近太阳校正（连续，无硬切削）
def aureole_penalty_mag(D_deg, eps_deg, g=0.80, A0=1.5, D0=2.0):

    # 수치 안전 및 각도 준비
    #数值安全和角度准备
    eps = min(max(float(eps_deg), AUREOLE_EPS_MIN), AUREOLE_EPS_MAX)
    mu  = math.cos(math.radians(eps))

    # HG phase function (정규화: 90°에서 1이 되도록) 规范化：从90°到1
    P   = (1.0 - g*g) / pow(1.0 + g*g - 2.0*g*mu, 1.5)
    P90 = (1.0 - g*g) / pow(1.0 + g*g, 1.5)
    R   = P / P90              # eps→작을수록 R>1 (근태양 밝아짐)

    # 태양이 낮게 잠길수록(큰 D) 오레올 급감: w(D)=exp(-D/D0)
    D = max(0.0, float(D_deg)) # 태양 위에 있으면 D=0으로 간주(=최대 오레올)
    w = math.exp(-D / D0)

    # 밝기 증가 비율을 등급 페널티로 변환 (Koomen '평균' 대비 방향성 부스트)
    # R=1이면 0mag, R≫1이면 양의 페널티가 커짐
    return 2.5 * math.log10(1.0 + A0 * w * max(0.0, R - 1.0))
if not hasattr(math, 'isfinite'):
    def _isfinite(x):
        return (not math.isinf(x)) and (not math.isnan(x))
    math.isfinite = _isfinite
# ---- Altitude bias policy ---- 'kv_only' or 'full'
ALTITUDE_BIAS = 'full'

# 사이트 불변 모드: 기하/배경/공기질량 계산엔 alt=0.0만 쓰도록 강제
SITE_INVARIANT = False

def _alt_eff_geom(alt_m):
    # 기하(alt/az, D)와 rise/set 경계 계산용 고도
    return 0.0 if (SITE_INVARIANT or ALTITUDE_BIAS == 'kv_only') else float(alt_m)

def _alt_for_bg(alt_m):
    # 배경밝기(황혼 μV, 잔광 등) 계산용 고도
    return 0.0 if (SITE_INVARIANT or ALTITUDE_BIAS == 'kv_only') else float(alt_m)

def _press_gain_for_afterglow():
    return 0.0 if (SITE_INVARIANT or ALTITUDE_BIAS == 'kv_only') else float(TWILIGHT_PRESS_GAIN)

# ==== Swiss Ephemeris rise/set options ====
SE_USE_REFRACTION = True       # 굴절 보정 사용(기압/온도 반영). 끄려면 False.
SE_USE_DISC_BOTTOM = False     # True면 태양 '하단' 기준, False면 '중심' 기준
SE_ATPRESS = 1013.25           # hPa (SE_USE_REFRACTION=True일 때만 사용)
SE_ATTEMP  = 20.0              # °C
SE_ATHUM   = 0.63               # 상대습도 0..1 (요구하는 래퍼가 있음)
# ==== 굴절 모드 & P/T 추정(ISA troposphere) ================================
# 모드: 'off'|'sea'|'alt'|'custom'
REFRACTION_MODE = 'alt'
REFR_P_HPA_DEFAULT = SE_ATPRESS
REFR_T_C_DEFAULT   = SE_ATTEMP

def _temp_from_altitude_c(h_m):
    # 표준대기: 15°C @ SL, lapse rate 6.5 K/km (대류권); 하한 -56.5°C
    t = 15.0 - 6.5*(float(h_m)/1000.0)
    return t if t >= -56.5 else -56.5

def _press_from_altitude_hpa(h_m):
    # 표준대기 기압(해발 h[m], ~11km까지 유효)
    h = float(h_m)
    return 1013.25 * (1.0 - 2.25577e-5*h)**5.2559 if h >= 0.0 else 1013.25

def _refr_params(mode, alt_m, p_custom=None, t_custom=None):
    m = (mode or 'off').lower()
    if m == 'off':
        return 0.0, 0.0
    if m == 'sea':
        return float(REFR_P_HPA_DEFAULT), float(REFR_T_C_DEFAULT)
    if m == 'alt':
        return _press_from_altitude_hpa(alt_m), _temp_from_altitude_c(alt_m)
    # 'custom'
    p = REFR_P_HPA_DEFAULT if p_custom is None else p_custom
    t = REFR_T_C_DEFAULT   if t_custom is None else t_custom
    return float(p), float(t)
# ========================================================================

# ==== Sea-level (Maryland) twilight μV anchors (V band) ====
# Source: Koomen et al. (1952) Maryland (sea-level) converted to mag/arcsec^2 by Nawar (2020), Table 5.
# Examples cited in paper: D=6° → 13.1 mag/arcsec^2; D=12° → 19.786; D=15° → 20.979.
# We extend to 18° by saturating to sea-level dark sky ~21.36 mag/arcsec^2.
TWILIGHT_MODEL = 'patat_poly'   
# --- Paranal (Patat 2006) parameters ---
PARANAL_ALT_M   = 2635.0   # Paranal 고도[m] (≈2635 m)
# Patat 2006 (V band), ζ(태양 천정거리, deg) 95–105° 유효: b(ζ)=a0+a1(ζ-95)+a2(ζ-95)^2
PATAT_V_A0 = 11.84
PATAT_V_A1 = 1.518
PATAT_V_A2 = -0.057
# ==== Visibility model switch ====
# 'legacy'      : 기존( Koomen+방위가중+근지평 감점 )
# 'mag_aureole' : A안만 적용(기존 + HG 오레올 페널티)
# 'contrast'    : B안만 적용(베일광 기반 대비 임계)
# 'hybrid'      : A안과 B안 둘 다 계산해서 더 보수적인 값을 사용
# 'unified'     : A안과 B안을 합침
VISIBILITY_MODEL = 'unified'

# ---- A안(HG 오레올) 튜닝값 (aureole_penalty_mag에 전달되는 기본값과 동일) ----
AUREOLE_G   = 0.8   
AUREOLE_A0  = 2.5   
AUREOLE_D0  = 2.0 
AUREOLE_EPS_MIN = 0.0
AUREOLE_EPS_MAX = 90.0 
# 목표물 대비 손실 스케일(ε 커지면 급감) — 행성별 과적합 없이 보편 파라미터
AUREOLE_TARGET_K = 1.5    # (수성↓, 금성↑ 조절 레버)
AUREOLE_EPS_C    = 16.0   # 전이 스케일[deg] (ε ≳ 해당값°면 HG 벌점 급감)
AUREOLE_Q        = 1.5    # 급감 가파름
# --- 오레올 이각 대역 가중 ---
AUREOLE_BAND_LO   = 0.0    # 시작
AUREOLE_BAND_HI   = 9.0    # 끝
# 경계 완화 폭(부드럽게 오르내리는 구간 폭)
AUREOLE_BAND_WLO  = 1.0    # 4° 아래에서 서서히 올라오기
AUREOLE_BAND_WHI  = 20.0    # 8° 이후 서서히 줄어들기
AUREOLE_BAND_GAIN = 1.0    # 밴드 가중 전체 스케일(보통 1.0)

def _eps_band_weight(eps,
                     lo=AUREOLE_BAND_LO, hi=AUREOLE_BAND_HI,
                     wlo=AUREOLE_BAND_WLO, whi=AUREOLE_BAND_WHI,
                     gain=AUREOLE_BAND_GAIN):
    """
    0..lo-wlo        : 0
    lo-wlo..lo+wlo   : smoothstep로 0→1
    lo+wlo..hi-whi   : 1 (플래토)
    hi-whi..hi+whi   : smoothstep로 1→0
    hi+whi..∞        : 0
    """
    e = max(0.0, float(eps))
    # 상승 에지
    if e <= (lo - wlo):
        rise = 0.0
    elif e >= (lo + wlo):
        rise = 1.0
    else:
        t = (e - (lo - wlo)) / max(1e-6, 2.0*wlo)
        rise = _smoothstep01(t)  # C¹

    # 하강 에지
    if e <= (hi - whi):
        fall = 1.0
    elif e >= (hi + whi):
        fall = 0.0
    else:
        t = ((hi + whi) - e) / max(1e-6, 2.0*whi)
        fall = _smoothstep01(t)  # C¹

    return gain * rise * fall

def aureole_target_penalty_mag(D_deg, eps_deg,
                               g=None, A0=None, D0=None,
                               k=None, eps_c=None, q=None):
    """
    HG 기반 '표적 대비 손실' 벌점[mag].
    UI 노브(AUREOLE_*)를 실시간 반영하기 위해 디폴트는 None으로 두고
    본문에서 전역 상수를 읽는다.
    """
    if g is None:      g = AUREOLE_G
    if A0 is None:     A0 = AUREOLE_A0
    if D0 is None:     D0 = AUREOLE_D0
    if k is None:      k = AUREOLE_TARGET_K
    if eps_c is None:  eps_c = AUREOLE_EPS_C
    if q is None:      q = AUREOLE_Q

    base = aureole_penalty_mag(D_deg, eps_deg, g=g, A0=A0, D0=D0)
    damp = k * math.exp(- (max(0.0, float(eps_deg)) / max(1e-6, float(eps_c))) ** float(q))
    w_eps = _eps_band_weight(eps_deg)
    return max(0.0, _eps_band_weight(eps_deg) * base * damp)

# ---- B안(대비 임계: 베일광) 튜닝값 ----
VEIL_K      = 16.0   
VEIL_THETA0 = 1.0  
VEIL_P      = 2.0   
VEIL_D0     = 1.0 # 태양 침강각 감쇠 e-폴드(베일광의 D 의존성)
# ---- μV [mag/arcsec^2] ↔ L [cd/m^2] 변환 (Crumey 2014) ----
def muV_to_luminance_cd_m2(muV):
    # B[cd/m^2] = 10^((12.58 - μV)/2.5)
    return 10.0 ** ((12.58 - float(muV)) / 2.5)

def luminance_cd_m2_to_muV(B):
    # μV = -2.5 log10(B) + 12.58
    B = max(1e-12, float(B))
    return -2.5 * math.log10(B) + 12.58
def nelm_from_muV(muV, F=2.0):
    # m_lim ≈ 0.426·μV − 2.365 − 2.5·log10(F)  (mlim_base 내부식 분리)
    return 0.426 * float(muV) - 2.365 - 2.5 * math.log10(max(1e-6, float(F)))
# --- Moonlight sky brightness (Krisciunas & Schaefer 1991) -------------------
NLAMBERt_TO_CD_M2 = 3.183098861837907e-6  # 1 nL = 3.1831e-6 cd/m^2

def _ang_sep_altaz(alt1_deg, az1_deg, alt2_deg, az2_deg):
    a1 = math.radians(float(alt1_deg)); A1 = math.radians(float(az1_deg))
    a2 = math.radians(float(alt2_deg)); A2 = math.radians(float(az2_deg))
    # 구면코사인법칙 (고도/방위 → 천구상 각거리)
    return math.degrees(math.acos(
        max(-1.0, min(1.0,
            math.sin(a1)*math.sin(a2) +
            math.cos(a1)*math.cos(a2)*math.cos(A1 - A2)
        ))
    ))

def moon_luminance_cd_m2(jd_ut, lon, lat, alt_m, alt_target_deg, az_target_deg, kv=None):
    """
    달빛이 만드는 배경 하늘 밝기 L_moon [cd/m^2] (항상 가산).
    - K&S(1991) 근사식:
        I(α) = 10^(-0.4*(3.84 + 0.026|α| + 4e-9 α^4))
        f(ρ) = 10^(5.36)*(1.06 + cos^2 ρ) + 10^(6.15 - ρ/40)
        B_nL = I * f(ρ) * 10^(-0.4*k*X_moon) * (1 - 10^(-0.4*k*X_sky))
    L_moon = B_nL * (nL→cd/m^2)
    - 입력 alt_target/az_target는 관측 시선(행성 위치).
    - 달이 지평선 아래면 0 처리.
    """
    alt_moon, az_moon = altaz_of_body(jd_ut, astrology.SE_MOON, lon, lat, alt_m)
    if alt_moon <= 0.0:
        return 0.0

    # 위상각 α (deg)
    try:
        rflag, ph, serr = swe_pheno_ut_ex(jd_ut, astrology.SE_MOON, astrology.SEFLG_SWIEPH)
        alpha = abs(float(ph[0]))
    except Exception:
        alpha = 0.0

    # 공기질량과 소광계수
    if kv is None:
        kv = kV_from_altitude(alt_m)
    X_moon = airmass_effective(max(0.0, float(alt_moon)), alt_m)
    X_sky  = airmass_effective(max(0.0, float(alt_target_deg)), alt_m)

    # 달과 시선 사이 각거리 ρ
    rho = _ang_sep_altaz(alt_target_deg, az_target_deg, alt_moon, az_moon)
    rho = max(0.0, min(180.0, float(rho)))
    cr  = math.cos(math.radians(rho))

    # K&S 구성요소
    I_alpha = 10.0 ** (-0.4 * (3.84 + 0.026*alpha + 4.0e-9*(alpha**4)))
    f_rho   = (10.0**5.36) * (1.06 + cr*cr) + (10.0 ** (6.15 - rho/40.0))
    B_nL    = I_alpha * f_rho * (10.0 ** (-0.4*kv*X_moon)) * (1.0 - 10.0 ** (-0.4*kv*X_sky))
    L_cd_m2 = max(0.0, B_nL * NLAMBERt_TO_CD_M2)
    return L_cd_m2
# ---------------------------------------------------------------------------

def veiling_luminance_stiles_holladay(D_deg, eps_deg,
                                      K=None, D0=None, theta0=None):
    """
    Stiles–Holladay 형태의 베일광 L_v (cd/m^2).
    UI 노브(VEIL_*)가 실시간 반영되도록 None → 전역 상수 대입.
    """
    if K is None:       K = VEIL_K
    if D0 is None:      D0 = VEIL_D0   # 아래 1줄짜리 새 상수 추가 권장
    if theta0 is None:  theta0 = VEIL_THETA0

    D   = max(0.0, float(D_deg))
    eps = max(float(eps_deg), float(theta0))
    w = 1.0 if (D0 is None or float(D0) <= 0.0) else math.exp(-D/float(D0))
    return float(K) * w / (eps**VEIL_P)

def mlim_from_contrast(D, dA_deg, eps_deg, alt_m, L_moon_cd_m2=0.0):
    # 1) μV(D): 현재 모델 사용
    mu_site = muV_twilight_site(float(D), alt_m)

    # 2) 베일광 + 달빛 → 실효 배경
    B_site  = muV_to_luminance_cd_m2(mu_site)
    L_v     = veiling_luminance_stiles_holladay(D, eps_deg)  # cd/m^2
    B_eff   = B_site + L_v + max(0.0, float(L_moon_cd_m2))
    mu_eff  = luminance_cd_m2_to_muV(B_eff)

    # 3) 베일광 '추가' 밝기만 감점: dmu_veil = μ_site - μ_eff ≥ 0
    dmu_veil = max(0.0, mu_site - mu_eff)
    base  = 0.5 * (1.0 + math.cos(math.radians(dA_deg)))
    w_az  = base ** AZ_WEIGHT_P
    return mlim_base(D) - C_MU2NELM * dmu_veil * w_az

def mlim_unified(D, dA_deg, eps_deg, alt_m, L_moon_cd_m2=0.0, F=2.0):
    """
    물리 일관 통합식(+달빛 상시 가산):
      1) μ_site(D, alt) 산출 (황혼 기본 밝기)
      2) veiling L_v(D, ε) 추가
      3) L_moon(달빛) 추가  ← (항상)
      4) μ_eff ← B_eff
      5) NELM_bg = μ_eff → NELM 변환
      6) 표적 대비 손실 Δm_a (HG) 차감
    """
    # 1) site 황혼 밝기
    mu_site = muV_twilight_site(float(D), float(alt_m))
    B_site  = muV_to_luminance_cd_m2(mu_site)

    # 2) veiling (방위 가중 포함)
    base = 0.5 * (1.0 + math.cos(math.radians(dA_deg)))  # 0..1
    w_az = base ** AZ_WEIGHT_P
    L_v  = veiling_luminance_stiles_holladay(D, eps_deg) * w_az

    # 3) 달빛 상시 가산
    B_eff = B_site + L_v + max(0.0, float(L_moon_cd_m2))
    mu_eff = luminance_cd_m2_to_muV(B_eff)

    # 4) 배경 기준 NELM
    m_bg = nelm_from_muV(mu_eff, F=F)

    # 5) 표적 대비 손실(HG)
    m_a = aureole_target_penalty_mag(D, eps_deg)

    NELM_FLOOR = -8.0
    m_eff = min(TARGET_NELM_DARK, m_bg - m_a)
    return m_eff

MU_DARK_SEA = 21.36            # sea-level dark-sky μV (Paranal ~21.7 → sea-level ≈21.36, Δ~0.34)
C_MU2NELM   = 0.426            # μV 차이를 맨눈 한계 감점(mag)으로 환산하는 계수(Crumey)

# Maryland (sea-level) μV(D) anchors at 1° steps (D in degrees of solar depression, 6..18)
TWILIGHT_ANCHORS_MD_V = [
    (6.0, 13.100), (7.0, 14.612), (8.0, 15.966), (9.0, 17.160),
    (10.0, 18.194), (11.0, 19.070), (12.0, 19.786), (13.0, 20.343),
    (14.0, 20.741), (15.0, 20.979), (16.0, 21.058), (17.0, 21.209),
    (18.0, 21.360)
]
def muV_patat_paranal(D):
    """
    Paranal(≈743 hPa)에서의 황혼 표면밝기 μV(D) [mag/arcsec^2]
    - Patat 2006 V-band 다항식: ζ=95..105°(D=5..15°) 유효
    - D>15°: Paranal 암야로 포화(부드럽게 clamp)
    - D<5°: 본 코드에서는 afterglow 자체가 D<6°에서 0 처리이므로 실사용 경로 아님
    """
    z = 90.0 + float(D)                # solar zenith angle ζ
    x = (max(95.0, min(105.0, z)) - 95.0)
    mu = PATAT_V_A0 + PATAT_V_A1*x + PATAT_V_A2*(x*x)

    # 상한 포화: D≥15°(ζ≥105°)에선 Paranal 암야보다 어두워지지 않게 clamp
    mu_dark_paranal = MU_DARK_SEA + delta_mu_press_vs_sea(PARANAL_ALT_M)
    if z >= 105.0:
        mu = min(mu, mu_dark_paranal)
    return float(mu)

def muV_patat_site(D, alt_m):
    mu_par   = muV_patat_paranal(D)
    alt_b    = _alt_for_bg(alt_m)
    p_site   = pressure_from_altitude_hpa(alt_b)
    p_par    = pressure_from_altitude_hpa(PARANAL_ALT_M)
    dmu_press = -2.5 * math.log10(max(1e-9, p_site / p_par))
    return mu_par + (0.0 if ALTITUDE_BIAS == 'kv_only' else dmu_press)

def muV_twilight_site(D, alt_m):
    alt_b = _alt_for_bg(alt_m)
    if TWILIGHT_MODEL == 'patat_poly':
        return muV_patat_site_ext(D, alt_b)
    return muV_md_site(D, alt_b)

def _interp1d_anchor(anchors, x):
    """Piecewise-linear interpolation on list[(x, y)], clamped to ends."""
    if not anchors:
        return None
    if x <= anchors[0][0]:
        return anchors[0][1]
    if x >= anchors[-1][0]:
        return anchors[-1][1]
    for i in range(len(anchors) - 1):
        x1, y1 = anchors[i]
        x2, y2 = anchors[i+1]
        if x1 <= x <= x2:
            t = (x - x1) / float(x2 - x1)
            return y1 + t * (y2 - y1)
    return anchors[-1][1]

def muV_md_sea(D):
    """Maryland sea-level μV(D) from anchors (mag/arcsec^2)."""
    return _interp1d_anchor(TWILIGHT_ANCHORS_MD_V, float(D))

def muV_md_site(D, alt_m):
    mu_sea = muV_md_sea(D)
    if ALTITUDE_BIAS == 'kv_only':
        dmu = 0.0
    else:
        dmu = delta_mu_press_vs_sea(alt_m)
    return mu_sea + dmu

INNER_PLANETS  = set([astrology.SE_MERCURY, astrology.SE_VENUS])
OUTER_PLANETS  = set([astrology.SE_MARS, astrology.SE_JUPITER, astrology.SE_SATURN])

# ==== Sea-level baseline & pressure (altitude) scaling for twilight ====
SEA_LEVEL_HPA    = 1013.25  # 해수면 표준기압
TWILIGHT_D_MIN   = 0.0      # 잔광 모델이 작동하는 D 범위
TWILIGHT_D_MAX   = 30.0
TWILIGHT_C       = 0.55     # 잔광 감점 스케일(안정적 디폴트)
AZ_WEIGHT_P      = 1.75     # 방위 가중 지수: w=(0.5*(1+cos dA))^p
TWILIGHT_PRESS_GAIN = 1.0   # 압력(고도) 보정이 잔광 감점에 주는 1:1 감쇠

def pressure_from_altitude_hpa(alt_m, p0=SEA_LEVEL_HPA):
    # 저층 대기 근사: p = p0 * (1 - 2.25577e-5*h)^5.25588
    h = float(max(0.0, alt_m))
    return p0 * (1.0 - 2.25577e-5*h)**5.25588

def delta_mu_press_vs_sea(alt_m):
    """
    해수면 대비 '딥 트와일라이트' 하늘밝기 차이(양수면 더 어둡다, mag/arcsec^2).
    Δμ = -2.5 log10(p_site / p_sea)
    """
    p_site = pressure_from_altitude_hpa(alt_m)
    return -2.5 * math.log10(max(1e-9, p_site / SEA_LEVEL_HPA))

def is_inner(ipl):
    return ipl in INNER_PLANETS

def is_outer(ipl):
    return ipl in OUTER_PLANETS

# --- Twilight time windows (hours from sunset/sunrise) ---
EVENING_WINDOW_HR = 6.0   # 일몰 후 스캔시간
MORNING_WINDOW_HR = 6.0   # 일출 전 스캔시간

# --- Near-horizon gating for heliacal phenomena ---
D_NEAR_MIN = 0.0   # 태양 침강각 하한
D_NEAR_MAX = 30.0   # 태양 침강각 상한
H_NEAR_MIN = 0.0    # 지평선 '위'만 잡고 싶으면 0.0
H_NEAR_MAX = 10.0    # 지평선 위 10도까지

PLANET_IDS = [
    astrology.SE_SATURN,
    astrology.SE_JUPITER,
    astrology.SE_MARS,
    astrology.SE_VENUS,
    astrology.SE_MERCURY,
]

PLANET_NAMES = {
    astrology.SE_SATURN: u"Saturn",
    astrology.SE_JUPITER: u"Jupiter",
    astrology.SE_MARS:   u"Mars",
    astrology.SE_VENUS:  u"Venus",
    astrology.SE_MERCURY:u"Mercury",
}

# Approx reference magnitudes for m = Href + 5*log10(r*Δ) + phase
HREF = {
    astrology.SE_MERCURY: -0.60,
    astrology.SE_VENUS:   -4.40,
    astrology.SE_MARS:    -1.52,
    astrology.SE_JUPITER: -9.40,
    astrology.SE_SATURN:  -8.88,
}

# --- Atmospheric extinction (V-band), altitude-only model ---
KV0_SEA = 0.30      # sea-level reference (mag per airmass)
H0_M    = 8000     # scale height in meters
KV_USED = 0.30
def kV_from_altitude(H_m, kv0_sea=KV0_SEA, h0_m=H0_M,
                     clamp_min=None, clamp_max=None):
    """
    Altitude-only model: kV(H) = KV0_SEA * exp(-H / H0_M)
    clamp_*: optional safety bounds (set to None to disable)
    """
    import math
    kv = float(kv0_sea) * math.exp(-float(H_m) / float(h0_m))
    if clamp_min is not None:
        kv = max(clamp_min, kv)
    if clamp_max is not None:
        kv = min(clamp_max, kv)
    return kv
# ==== AIRMASS backends (near-horizon ready) ====
# 사용 옵션: 'kivalov' | 'pickering' | 'kasten-young' | 'hybrid'
AIRMASS_MODEL = 'kivalov'         # hybrid: 수평선 근처 Kivalov, 그 밖은 Kasten–Young
AIRMASS_HYBRID_SWITCH_DEG = 3.0   # h <= 3° 에서는 Kivalov로 전환
AIRMASS_H_M     = 7640.0          # 단층 지수 대기 스케일 높이 [m]
AIRMASS_N0M1    = 2.9e-4          # (n0-1) at sea-level (가시광 근사)
AIRMASS_DR_M    = 200.0           # 적분 셸 두께 [m]
AIRMASS_CLAMP_MAX = None          # 안전상 X 상한(원하면 None 또는 더 크게)

def airmass_pickering2002(alt_deg):
    """Pickering (2002) 근사식: 수평선 근처에서 K-Y보다 안정적인 닫힌형."""
    h = max(0.0, float(alt_deg))
    # X = 1 / sin(h + 244/(165 + 47 h^1.1))
    return 1.0 / math.sin(math.radians(h + 244.0 / (165.0 + 47.0 * (h**1.1 + 1e-16))))

def _kivalov_raytrace_core(alt_deg, elev_m, R_earth_m=6371000.0,
                           H_m=AIRMASS_H_M, n0_minus1=AIRMASS_N0M1,
                           h_top_m=120000.0, dr_m=AIRMASS_DR_M):
    """
    Kivalov 스타일 레이-트레이싱: 구면 대기에서 스넬 불변량으로 광로 적분.
    반환: 상대 공기질량 X (sea-level ρ0 기준)
    """
    hdeg = float(alt_deg)
    if hdeg <= -1.0:
        return 0.0
    z = math.radians(90.0 - hdeg)           # apparent zenith angle
    r0 = R_earth_m + float(elev_m)

    def rho_ratio(h_m):
        return math.exp(-h_m / float(H_m))
    def n_of_r(r_m):
        h = r_m - R_earth_m
        return 1.0 + n0_minus1 * rho_ratio(h)

    n0_local = n_of_r(r0)               # 관측고도에서의 굴절률로 시드
    I = n0_local * r0 * math.sin(z)

    X = 0.0
    r = r0
    while r < (R_earth_m + h_top_m):
        n = n_of_r(r)
        s_sin = I / (n * r)
        if s_sin >= 1.0:
            s_sin = 0.999999999
        elif s_sin <= -1.0:
            s_sin = -0.999999999
        theta = math.asin(s_sin)
        cos_t = math.cos(theta)
        if cos_t <= 1e-12:
            break
        ds = dr_m / cos_t
        rr = rho_ratio(r - R_earth_m)
        X += rr * ds
        r += dr_m
        if rr < 1e-6 and r > r0 + 10000.0:
            break

    col_vert = float(H_m) * math.exp(-float(elev_m) / float(H_m))  # 관측 고도의 수직 기둥
    X /= max(1e-9, col_vert) 
    if AIRMASS_CLAMP_MAX is not None:
        X = min(X, float(AIRMASS_CLAMP_MAX))
    return max(0.0, X)

# 캐싱: alt(0.01°), 고도(0.1 m) 격자에 캐시해 반복 호출 속도 ↑
@lru_cache(maxsize=262144)
def _kivalov_cached(h_q, elev_q, H_m, n0m1, dr_m):
    return _kivalov_raytrace_core(h_q, elev_q, H_m=H_m, n0_minus1=n0m1, dr_m=dr_m)

def airmass_kivalov_raytrace(alt_deg, elev_m,
                             H_m=AIRMASS_H_M, n0_minus1=AIRMASS_N0M1, dr_m=AIRMASS_DR_M):
    h_q = round(max(0.0, float(alt_deg)), 2)   # 0.01°
    e_q = round(float(elev_m), 1)              # 0.1 m
    return _kivalov_cached(h_q, e_q, float(H_m), float(n0_minus1), float(dr_m))

def airmass_effective(alt_deg, elev_m, model=None):
    elev_eff = 0.0 if (SITE_INVARIANT or ALTITUDE_BIAS == 'kv_only') else float(elev_m)
    m = (AIRMASS_MODEL if model is None else model).lower()
    h = max(0.0, float(alt_deg))
    if m == 'hybrid':
        return airmass_kivalov_raytrace(h, elev_eff) if h <= AIRMASS_HYBRID_SWITCH_DEG else airmass_kasten_young(h)
    elif m == 'kivalov':
        return airmass_kivalov_raytrace(h, elev_eff)
    elif m == 'pickering':
        return airmass_pickering2002(h)
    else:
        return airmass_kasten_young(h)

def airmass_kasten_young(h_deg):
    z = max(0.0, 90.0 - h_deg)
    return 1.0 / (math.cos(math.radians(z)) + 0.50572 * (96.07995 - z)**-1.6364)

# 암야(천문박명 끝) 목표 맨눈 한계
TARGET_NELM_DARK = 6.0

def mlim_base(D, F=2.0):
    """
    박명 각도 D(°)를 하늘 표면밝기 μV(D)로 평가한 뒤,
    μV→맨눈 한계(NELM)로 직접 변환하는 연속 수식 버전.
    - TWILIGHT_MODEL == 'patat_poly'  : Patat 다항식(사이트=해수면) 확장 사용
    - TWILIGHT_MODEL == 'md_anchor'   : Maryland sea-level 앵커 보간 사용
    - 기타(ex. 'exp_simple')          : 기존 선형 보간 폴백 유지
    매개변수:
      F : field factor(관측 조건 계수). 평균 2.0 정도.
    반환:
      NELM [mag] (2.0..TARGET_NELM_DARK로 클램프)
    """
    d = float(D)

    # μV(D): sea-level 기준
    if TWILIGHT_MODEL == 'patat_poly':
        mu = muV_patat_site_ext(d, 0.0)      # sea-level(0 m)로 강제
    elif TWILIGHT_MODEL == 'md_anchor':
        # 앵커는 6..18°만 정의되어 있으므로 구간 밖은 가장자리로 클램프
        mu = muV_md_sea(max(6.0, min(18.0, d)))
    else:
        # 폴백: 기존 선형 보간(이하 그대로 유지)
        if d <= 6.0:
            return 2.0
        if d >= 18.0:
            return TARGET_NELM_DARK
        if d <= 9.0:
            t = (d - 6.0) / 3.0
            return 2.0 + t * (4.5 - 2.0)
        if d <= 12.0:
            t = (d - 9.0) / 3.0
            return 4.5 + t * (6.0 - 4.5)
        t = (d - 12.0) / 6.0
        return 6.0 + t * (TARGET_NELM_DARK - 6.0)

    # μV → NELM 변환
    # m_lim ≈ 0.426·μV − 2.365 − 2.5·log10(F)
    m_lim = 0.426 * float(mu) - 2.365 - 2.5 * math.log10(max(1e-6, float(F)))

    # 상/하한 클램프
    if d >= 18.0:
        return min(TARGET_NELM_DARK, m_lim)
    return max(6.0, min(m_lim, TARGET_NELM_DARK))

def afterglow(D, dA_deg, is_evening, alt_m):
    if D < 0.0 or D > 18.0:
        return 0.0
    d = float(D)

    base = 0.5 * (1.0 + math.cos(math.radians(dA_deg)))
    w_az = base ** AZ_WEIGHT_P

    if TWILIGHT_MODEL == 'md_anchor':
        mu_site = muV_md_site(d, _alt_for_bg(alt_m))
        MU_DARK = MU_DARK_SEA  
        dmu = max(0.0, MU_DARK - mu_site)
        return C_MU2NELM * TWILIGHT_C * dmu * w_az

    elif TWILIGHT_MODEL == 'patat_poly':
        mu_site = muV_patat_site(d, _alt_for_bg(alt_m))
        MU_DARK = MU_DARK_SEA  
        dmu = max(0.0, MU_DARK - mu_site)
        return C_MU2NELM * TWILIGHT_C * dmu * w_az

    else:
        D0, gamma = 5.0, 1.2
        x = math.exp(- (d / D0) ** gamma)
        ag0 = TWILIGHT_C * x * w_az
        dmu = delta_mu_press_vs_sea(_alt_for_bg(alt_m))  
        ag  = max(0.0, ag0 - _press_gain_for_afterglow() * dmu)
        return ag

# --- helpers ---
def _smoothstep01(t):  # 0..1 -> S-curve
    t = max(0.0, min(1.0, t))
    return t*t*(3.0 - 2.0*t)

def _patat_poly_mu_slope_paranal(D):
    """Paranal 기준 Patat 다항식의 μ와 dμ/dD [mag/deg]"""
    z = 90.0 + float(D)             # solar zenith angle
    x = z - 95.0
    mu = PATAT_V_A0 + PATAT_V_A1*x + PATAT_V_A2*(x*x)
    slope = PATAT_V_A1 + 2.0*PATAT_V_A2*x  # dμ/dD
    return mu, slope

# --- extended Patat μV(D) for any D (we care about ~5..18) ---
def muV_patat_site_ext(D, alt_m):
    D = float(D)
    alt_b = _alt_for_bg(alt_m)

    if D >= 15.0:
        mu15_par, slope15 = _patat_poly_mu_slope_paranal(15.0)
        dmu_press = 0.0 if ALTITUDE_BIAS == 'kv_only' else -2.5 * math.log10(
            pressure_from_altitude_hpa(alt_b) / pressure_from_altitude_hpa(PARANAL_ALT_M)
        )
        mu15_site   = mu15_par + dmu_press
        mu_dark_site = MU_DARK_SEA if ALTITUDE_BIAS == 'kv_only' \
                        else (MU_DARK_SEA + delta_mu_press_vs_sea(alt_b))

        tau = max(0.2, (mu_dark_site - mu15_site) / max(1e-6, slope15))
        mu_tail = mu15_site + (mu_dark_site - mu15_site) * (1.0 - math.exp(-(D - 15.0)/tau))
        return mu_tail if D < 18.0 else mu_dark_site

    if D < 0.0:
        mu_patat = muV_patat_site(max(5.0, D), alt_b)
        mu_md    = muV_md_site(6.0, alt_b)
        w = _smoothstep01(D - 5.0)
        return (1.0 - w) * mu_patat + w * mu_md

    return muV_patat_site(D, alt_b)

# --- Swiss Ephemeris exact-output wrappers ---
@lru_cache(maxsize=262144)
def _swe_calc_ut_cached(jd_ut, ipl, flags):
    serr,xx,  = astrology.swe_calc_ut(
        float(jd_ut),
        int(ipl),
        int(flags)
    )
    # rflag는 Morinus 래퍼가 튜플을 줄 수 있으므로 그대로 보존한다.
    return 1, (float(xx[0]), float(xx[1]), float(xx[2])), ("" if serr is None else str(serr))

def swe_calc_ut_ex(jd_ut, ipl, flags):
    rflag, txx, serr = _swe_calc_ut_cached(jd_ut, ipl, flags)
    return 1, [txx[0], txx[1], txx[2]], serr

@lru_cache(maxsize=131072)
def _swe_pheno_ut_cached(jd_ut, ipl, flags):
    rflag, attr, serr = astrology.swe_pheno_ut(float(jd_ut), int(ipl), int(flags))
    # rflag 그대로 보존
    return rflag, tuple(float(a) for a in attr), ("" if serr is None else str(serr))

def swe_pheno_ut_ex(jd_ut, ipl, flags):
    rflag, tattr, serr = _swe_pheno_ut_cached(jd_ut, ipl, flags)
    return rflag, list(tattr), serr
def planet_magnitude(ipl, jd_ut):
    """
    Return (mV, {'r':..., 'Delta':..., 'R':..., 'elong':None, 'alpha':...})
    - Mercury/Venus/Mars/Jupiter: Mallama & Hilton 2018 (AA2018) V-band 근거식
    - Saturn: 링 효과 때문에 Swiss Ephemeris swe_pheno_ut의 V등급 사용
    """

    # 공통: Δ(지구-행성), R(지구-태양), r(행성-태양), 위상각 α
    rflag, pl_geo, serr = swe_calc_ut_ex(jd_ut, ipl, astrology.SEFLG_SWIEPH)
    Delta = pl_geo[2]

    rflag, sun_geo, serr = swe_calc_ut_ex(jd_ut, astrology.SE_SUN, astrology.SEFLG_SWIEPH)
    R = sun_geo[2]  # ≈1 AU

    rflag, pl_hel, serr = swe_calc_ut_ex(
        jd_ut, ipl,
        astrology.SEFLG_SWIEPH + astrology.SEFLG_HELCTR + astrology.SEFLG_TRUEPOS
    )
    r = pl_hel[2]

    # 위상각 α (law of cosines)
    cos_a = (r*r + Delta*Delta - R*R) / max(1e-9, 2.0*r*Delta)
    cos_a = max(-1.0, min(1.0, cos_a))
    alpha = math.degrees(math.acos(cos_a))

    def dist_term(r_AU, d_AU):
        return 5.0 * math.log10(max(1e-9, r_AU * d_AU))

    if ipl == astrology.SE_MERCURY:
        # Mallama 2018: V = H + 5log(rΔ) + Σ c_k α^k (k=1..6)
        a = alpha
        H = -0.613
        phase = ( 6.328e-2)*a + (-1.6336e-3)*a**2 + (3.3644e-5)*a**3 \
                + (-3.4265e-7)*a**4 + (1.6893e-9)*a**5 + (-3.0334e-12)*a**6
        mV = H + dist_term(r, Delta) + phase

    elif ipl == astrology.SE_VENUS:
        a = alpha
        H = -4.384
        if a <= 163.7:
            phase = (-1.044e-3)*a + (3.687e-4)*a**2 + (-2.814e-6)*a**3 + (8.938e-9)*a**4
        else:
            # cusp brightening 보정 구간
            phase = 240.44228 + (-2.81914)*a + (8.39034e-3)*a**2
        mV = H + dist_term(r, Delta) + phase

    elif ipl == astrology.SE_MARS:
        a = alpha
        H = -1.601
        if a <= 50.0:
            phase = (2.267e-2)*a + (-1.302e-4)*a**2
        else:
            phase = 1.234 + (-2.573e-2)*a + (3.445e-4)*a**2
        mV = H + dist_term(r, Delta) + phase

    elif ipl == astrology.SE_JUPITER:
        a = alpha
        H = -9.395
        if a <= 12.0:
            phase = (-3.7e-4)*a + (6.16e-4)*a**2
        else:
            x = a/180.0
            phase = -0.033 - 2.5*math.log10(
                max(1e-9, 1 - 1.507*x - 0.363*x**2 - 0.062*x**3 + 2.809*x**4 - 1.876*x**5)
            )
        mV = H + dist_term(r, Delta) + phase

    elif ipl == astrology.SE_SATURN:
        # 링 효과 반영: Swiss Ephemeris의 광도 그대로 사용
        try:
            rflag, ph, serr = swe_pheno_ut_ex(jd_ut, ipl, astrology.SEFLG_SWIEPH)
            # swe_pheno_ut: [phase_angle, phase_fraction, elongation, apparent_diam, magnitude, ...]
            mV = ph[4]
        except Exception:
            # 폴백: 간단한 위상 2차식 (정밀도 낮음)
            a = alpha
            H = -8.914
            phase = 2.446e-4*a + 2.672e-4*a**2 - 1.505e-6*a**3 + 4.767e-9*a**4
            mV = H + dist_term(r, Delta) + phase

    else:
        # 기타: 이전 테이블 유지(거의 사용 안 함)
        H0 = HREF.get(ipl, -1.0)
        mV = H0 + dist_term(r, Delta)

    return mV, {'r': r, 'Delta': Delta, 'R': R, 'elong': None, 'alpha': alpha}

def angular_sep_equ(ra1_deg, dec1_deg, ra2_deg, dec2_deg):
    a1 = math.radians(ra1_deg); d1 = math.radians(dec1_deg)
    a2 = math.radians(ra2_deg); d2 = math.radians(dec2_deg)
    cossep = math.sin(d1)*math.sin(d2) + math.cos(d1)*math.cos(d2)*math.cos(a1-a2)
    cossep = max(-1.0, min(1.0, cossep))
    return math.degrees(math.acos(cossep))

def elongation_deg(jd_ut, ipl):
    sra, sdec, _ = equ_coords(jd_ut, astrology.SE_SUN)
    pra, pdec, _ = equ_coords(jd_ut, ipl)
    return angular_sep_equ(pra, pdec, sra, sdec)

def altaz_of_body(jd_ut, ipl, lon, lat, alt_m):
    alt, az = altaz_cached(jd_ut, ipl, float(lon), float(lat), float(alt_m))
    return alt, az

def _find_crossing(jd0, jd1, target_alt_deg, lon, lat, alt_m):
    for _ in range(40):
        mid = 0.5*(jd0+jd1)
        # ★ 여기 교체
        alt = sun_altaz(mid, lon, lat, alt_m)[0]   # 고도만
        if alt > target_alt_deg:
            jd0 = mid
        else:
            jd1 = mid
    return 0.5*(jd0+jd1)

def _hemisphere_from_az(az_deg):
    # SwissEph az: 0=S, 90=W, 180=N, 270=E
    # E-hemisphere: within ±90° of 270°, W-hemisphere: 나머지
    d = ((az_deg - 270.0 + 540.0) % 360.0) - 180.0
    return 'E' if abs(d) <= 90.0 else 'W'

def _above_horizon_at(jd_ut, ipl, lon, lat, alt_m, eps=0.0):
    alt, az = altaz_of_body(jd_ut, ipl, lon, lat, alt_m)
    return (alt >= eps), alt, az

def _same_hemisphere_as_sun_at(jd_ut, ipl, lon, lat, alt_m):
    alt_s, az_s = sun_altaz(jd_ut, lon, lat, alt_m)
    alt_p, az_p = altaz_of_body(jd_ut, ipl, lon, lat, alt_m)
    return (_hemisphere_from_az(az_s) == _hemisphere_from_az(az_p))

@lru_cache(maxsize=262144)
def sun_altaz(jd_ut, lon, lat, alt_m):
    return altaz_of_body(jd_ut, astrology.SE_SUN, lon, lat, alt_m)

def _elong_side(jd_ut, ipl):
    pl = ecl_coords(jd_ut, ipl)               # (λ, β, Δ)
    sun = ecl_coords(jd_ut, astrology.SE_SUN)
    dlon = ((float(pl[0]) - float(sun[0]) + 540.0) % 360.0) - 180.0
    return 'E' if dlon > 0.0 else 'W'


def visible_window_for_day(jd_day_ut, lon, lat, alt_m, ipl, is_evening, hmin=0.0):
    """Return (any_visible, eps_min, near_horizon_flag, qual_twilight_visible)
       for that civil day's evening/morning window.
       qual_twilight_visible = 황혼-근지평-가시성(전이 검출용)"""
    sunset  = None
    sunrise = None
    # --- sunset/sunrise (Swiss Ephemeris) ---
    # 표준 일몰/일출을 스위스에페머리스로 구함(굴절 포함하려면 atpress/attemp 세팅)
    def _sun_event(jd0, lon, lat, alt_m, event):
        a = _alt_eff_geom(alt_m)
        key = (int(jd0), round(lon,12), round(lat,12), round(a,3),
            'disc_bottom' if SE_USE_DISC_BOTTOM else 'disc_center',
            'refract' if SE_USE_REFRACTION else 'no_refract', event)
        hit = _SUN_EVENT_CACHE.get(key)
        if hit is not None:
            return hit

        tjd_ut = _f(jd0 + 0.5)   # 하루 중간에서 시작(수렴성↑)
        lon    = _f(lon)
        lat    = _f(lat)
        alt_m  = _f(alt_m, 0.0)

        epheflag = astrology.SEFLG_SWIEPH | astrology.SEFLG_TOPOCTR
        rsmi = (astrology.SE_CALC_SET if event == 'set' else astrology.SE_CALC_RISE)
        rsmi |= (astrology.SE_BIT_DISC_BOTTOM if SE_USE_DISC_BOTTOM
                else astrology.SE_BIT_DISC_CENTER)
        if SE_USE_REFRACTION:
            atpress, attemp = _refr_params(REFRACTION_MODE, alt_m)
        else:
            atpress, attemp = 0.0, 0.0
        athum   = SE_ATHUM if SE_USE_REFRACTION else 0.0
        if not SE_USE_REFRACTION:
            rsmi |= astrology.SE_BIT_NO_REFRACTION

        geopos = (lon, lat, alt_m)
        horhgt = 0.0  # 로컬 지평선 고도(°)

        # 래퍼 호환: (tret, rflag) 또는 (rc, tret)
        rflag, jdev, serr = astrology.swe_rise_trans(
            float(tjd_ut), astrology.SE_SUN, "",
            int(epheflag), int(rsmi),
            float(lon), float(lat), float(a),      
            float(atpress), float(attemp))
        out = float(jdev) if (rflag >= 0) else None
        _SUN_EVENT_CACHE[key] = out    
        return out

    # --- 스캔 루프 (근지평/가시성/ε 동시 추적) ---
    def _scan(t_start, t_end, is_evening_flag, boundary_ok):
        if not boundary_ok:
            return False, 999.0, False, False
        step_min    = 1.0
        any_visible = False
        eps_min     = 999.0
        near_hz     = False
        qual_vis    = False
        t           = t_start
        # 창 제한시간은 각각의 설정을 따르도록
        limit_hours = (EVENING_WINDOW_HR if is_evening_flag else MORNING_WINDOW_HR)

        while t <= t_end and (t - t_start) <= (limit_hours/24.0):
            # 태양 고도/방위, 침강각
            alt_sun, az_sun = sun_altaz(t, lon, lat, alt_m)
            D = -alt_sun
            if is_evening_flag and (D > D_NEAR_MAX):
                break   # 저녁 창: 박명 범위를 지나 더 깊은 밤으로 가면 더는 볼 게 없음
            if (not is_evening_flag) and (D < D_NEAR_MIN):
                break   # 아침 창: 박명 범위 위로 올라오면 더는 볼 게 없음
            if D >= 0.0:  # 태양이 지평선 아래일 때만 검사
                # Twilight-range gate: skip heavy calc when sun depression outside [D_NEAR_MIN, D_NEAR_MAX]
                if not (D_NEAR_MIN <= D <= D_NEAR_MAX):
                    t += step_min/1440.0
                    continue
                # 행성 고도/방위
                alt_pl, az_pl = altaz_of_body(t, ipl, lon, lat, alt_m)

                # (A) 지평선 위?
                above_horizon_ok = (alt_pl >= 0.0)

                # (B) 태양과 같은 반구? (아침=E, 저녁=W)
                hemi_req = 'W' if is_evening_flag else 'E'
                hemi_ok  = (_hemisphere_from_az(az_sun) == hemi_req) and (_hemisphere_from_az(az_pl) == hemi_req)

                # ε(이각) 최소값 추적
                eps = elongation_deg(t, ipl)
                if eps < eps_min:
                    eps_min = eps

                # 근지평(황혼 장면 존재 여부)
                if above_horizon_ok and hemi_ok and (D_NEAR_MIN <= D <= D_NEAR_MAX) and (H_NEAR_MIN <= alt_pl <= H_NEAR_MAX):
                    near_hz = True

                # 가시성(밝기/잔광/지평선/소광)
                side_ok = (_elong_side(t, ipl) == ('E' if is_evening_flag else 'W'))
                if alt_pl >= hmin and side_ok:
                    dA = abs((az_pl - az_sun + 540.0) % 360.0 - 180.0)
                    kv = kV_from_altitude(alt_m)   # 고도 H에 따라 kV(H)=KV0_SEA*exp(-H/H0_M)
                    X  = airmass_effective(max(0.0, alt_pl), alt_m)
                    m0, _ = planet_magnitude(ipl, t)
                    # 달빛: K&S91 근사 (항상 계산해서 선형광도로 합산)
                    L_moon = moon_luminance_cd_m2(t, lon, lat, alt_m, alt_pl, az_pl, kv)
                    m_obs = m0 + kv * (X - 1.0)
                    # --- A안: Koomen(잔광) + HG 오레올(근태양 방향성) ---
                    m_lim_magA  = mlim_base(D) \
                                - afterglow(D, dA, is_evening_flag, alt_m) \
                                - aureole_penalty_mag(D, eps, g=AUREOLE_G, A0=AUREOLE_A0, D0=AUREOLE_D0) 

                    # --- B안: 대비 임계(베일광) ---
                    m_lim_contr = mlim_from_contrast(D, dA, eps, alt_m, L_moon)

                    # --- 모드 선택 ---
                    if   VISIBILITY_MODEL == 'legacy':
                        m_lim_eff = mlim_base(D) - afterglow(D, dA, is_evening_flag, alt_m)
                    elif VISIBILITY_MODEL == 'mag_aureole':
                        m_lim_eff = m_lim_magA
                    elif VISIBILITY_MODEL == 'contrast':
                        m_lim_eff = m_lim_contr
                    elif VISIBILITY_MODEL == 'unified':
                        m_lim_eff = mlim_unified(D, dA, eps, alt_m, L_moon_cd_m2=L_moon)
                    else:  # 'hybrid'
                        m_lim_eff = min(m_lim_magA, m_lim_contr)

                    if above_horizon_ok and (m_obs <= m_lim_eff):
                        any_visible = True
                        qual_vis = True

            t += step_min/1440.0

        return any_visible, eps_min, near_hz, qual_vis
    # 일몰/일출 시각 계산(실패하면 폴백 18:00/06:00)
    if sunset  is None: sunset  = _sun_event(jd_day_ut, lon, lat, alt_m, 'set')
    if sunrise is None: sunrise = _sun_event(jd_day_ut, lon, lat, alt_m, 'rise')
    if sunset  is None: sunset  = jd_day_ut + 0.75   # 최종 폴백(약 18:00)
    if sunrise is None: sunrise = jd_day_ut + 0.25   # 최종 폴백(약 06:00)

    # --- boundary gate: 경계 시점(일몰/일출)에서 '지평선 위' + '태양과 같은 동/서 반구'인지 확인 ---
    if is_evening:
        side_ok = (_elong_side(sunset, ipl) == 'E')   # 동이각=저녁
        return _scan(sunset, sunset + (EVENING_WINDOW_HR/24.0), True, side_ok)
    else:
        side_ok = (_elong_side(sunrise, ipl) == 'W')  # 서이각=아침
        return _scan(sunrise - (MORNING_WINDOW_HR/24.0), sunrise, False, side_ok)

def visibility_flags_around(chart, days_window=7):
    jd0 = chart.time.jd
    lon, lat, alt_m = chart.place.lon, chart.place.lat, float(chart.place.altitude)
    astrology.swe_set_topo(lon, lat, _alt_eff_geom(alt_m))
    out = {}
    scan_w = max(days_window, 10)

    for ipl in PLANET_IDS:
        # 임시 저장
        vis_e, vis_m = {}, {}
        qual_e, qual_m = {}, {}
        eps_e, eps_m = {}, {}
        near_e, near_m = {}, {}

        for dd in range(-scan_w, scan_w+1):
            jd = jd0 + dd
            ve, ee, ne, qe = visible_window_for_day(jd, lon, lat, alt_m, ipl, is_evening=True)
            vm, em, nm, qm = visible_window_for_day(jd, lon, lat, alt_m, ipl, is_evening=False)
            vis_e[dd], eps_e[dd], near_e[dd], qual_e[dd] = ve, ee, ne, qe
            vis_m[dd], eps_m[dd], near_m[dd], qual_m[dd] = vm, em, nm, qm
        def _deps_per_day(eps_seq, day):
            """ε의 일변화(대략 deg/day). 중앙차분 가능하면 사용."""
            has_prev = (day-1) in eps_seq
            has_next = (day+1) in eps_seq
            if has_prev and has_next:
                return 0.5 * (eps_seq[day+1] - eps_seq[day-1])
            if has_prev:
                return eps_seq[day] - eps_seq[day-1]
            if has_next:
                return eps_seq[day+1] - eps_seq[day]
            return 0.0

        def _persist_ok(qual_seq, day, is_first):
            """하루짜리 스파이크 스킵: First는 다음날, Last는 전날이 True여야."""
            return bool(qual_seq.get(day+1, False)) if is_first else bool(qual_seq.get(day-1, False))
        def _near_ok(near_seq, day):
            return any(near_seq.get(k, False) for k in (day-1, day, day+1))

        def find_first_last_dir(qual_seq, near_seq, eps_seq, is_evening, ipl):
            """
            전이 검출 + (내행성 전용) 방향성 체크 + 하루짜리 스파이크 스킵.
            - 저녁(EF/EL): EF는 dε/dt>0, EL은 dε/dt<0
            - 아침(MF/ML): MF는 dε/dt>0, ML은 dε/dt<0
            - 내행성만 방향성 적용. 외행성은 기존 규칙 그대로.
            """
            offs = sorted(qual_seq.keys())
            First = Last = None
            prev = qual_seq[offs[0]]

            inner = is_inner(ipl)

            for i in range(1, len(offs)):
                cur = qual_seq[offs[i]]

                # False -> True : First 후보 (EF 또는 MF)
                if (not prev) and cur and First is None:   # _near_ok/dir_ok/_persist_ok 모두 제거
                    First = offs[i]

                # True -> False : Last 후보 (EL 또는 ML)
                if prev and (not cur):
                    Last = offs[i-1]

                prev = cur

            return First, Last

        EF, EL = find_first_last_dir(qual_e, near_e, eps_e, True,  ipl)
        MF, ML = find_first_last_dir(qual_m, near_m, eps_m, False, ipl)
        # --- 여기서 외행성은 EF/ML 불허 규칙을 적용 ---
        if is_outer(ipl):
            EF = None  # 외행성의 Evening First 없음
            ML = None  # 외행성의 Morning Last 없음
        def _between_zero(a, b):
            if a is None or b is None:
                return False
            return (a <= 0 <= b) if a <= b else (b <= 0 <= a)
        def _contains_open(a, b, x=0):
            """열린 구간 (a, b)에 x가 들어가면 True. a/b None이면 False."""
            if a is None or b is None: return False
            if a == b: return False
            return (a < x < b) if a < b else (b < x < a)

        has_qual_today = bool(qual_e.get(0, False) or qual_m.get(0, False))

        if is_outer(ipl):
            # 외행성: EL→MF만
            combust_today = _contains_open(EL, MF)
        else:
            # 내행성: (EL→MF) 또는 (ML→EF)
            combust_today = _contains_open(EL, MF) or _contains_open(ML, EF)

        out[ipl] = {
            'combust': combust_today,
            'vis_evening': vis_e, 'vis_morning': vis_m,
            'qual_evening': qual_e, 'qual_morning': qual_m,
            'eps_evening': eps_e,  'eps_morning':  eps_m,
            'near_evening': near_e,'near_morning': near_m,
            'EF': EF, 'EL': EL, 'MF': MF, 'ML': ML,
            'AE': kV_from_altitude(alt_m),
        }
    return out