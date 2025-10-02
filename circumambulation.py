# circumambulation.py
# -*- coding: utf-8 -*-

from __future__ import division
import os, math, datetime
import io 
import astrology, chart, houses, mtexts
import mtexts
ASPECTS = (0, 60, 90, 120, 180)
DEFAULT_KEY_Y_PER_DEG = 1.0  # years per equatorial degree (OA)
DAYS_PER_YEAR = 365.2421897

_ASTROSEEK_CANDIDATES = [
    os.path.join(os.path.dirname(__file__), "data", "rt_0p5.txt"),
    os.path.join(os.path.dirname(__file__), "rt_0p5.txt"),
    os.path.join(os.getcwd(), "rt_0p5.txt"),
]
_GRID_PHI = None
_GRID_RT  = None

def _load_rt_table_once():
    global _GRID_PHI, _GRID_RT
    if _GRID_PHI is not None:
        return _GRID_PHI, _GRID_RT
    grid_phi, grid_rt = [], []
    def _try(path):
        if not os.path.exists(path):
            return False
        # 유니코드로 안전하게 읽고, 쉼표/세미콜론도 허용
        with io.open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if not line.strip():
                    continue
                parts = line.strip().replace("\t", " ")
                parts = parts.replace(",", " ").replace(";", " ").split()
                if len(parts) != 13:
                    continue
                try:
                    phi_txt = parts[0].replace(u"°", u"")
                    phi = float(phi_txt)
                    row = [float(x) for x in parts[1:13]]
                except Exception:
                    continue
                if phi > 66.0:
                    continue
                s = sum(row)
                if 300.0 <= s <= 420.0:
                    grid_phi.append(phi); grid_rt.append(row)
        return len(grid_phi) > 0
    for p in _ASTROSEEK_CANDIDATES:
        try:
            if _try(p):
                break
        except Exception:
            pass
    if not grid_phi:
        raise RuntimeError("Rising Times table not found. Put 'rt_0p5.txt' under ./data/ or project root.")
    pairs = sorted(zip(grid_phi, grid_rt), key=lambda t: t[0])
    _GRID_PHI = [p for p,_ in pairs]
    _GRID_RT  = [r for _,r in pairs]
    return _GRID_PHI, _GRID_RT

def _interp_rt12(phi):
    grid_phi, grid_rt = _load_rt_table_once()
    if phi <= grid_phi[0]:
        return list(grid_rt[0])
    if phi >= grid_phi[-1]:
        return list(grid_rt[-1])
    lo, hi = 0, len(grid_phi)-1
    while lo <= hi:
        mid = (lo+hi)//2
        if grid_phi[mid] < phi:
            lo = mid+1
        else:
            hi = mid-1
    i = lo
    if i <= 0:
        return list(grid_rt[0])
    if i >= len(grid_phi):
        return list(grid_rt[-1])
    p0, p1 = grid_phi[i-1], grid_phi[i]
    w = 0.0 if p1 == p0 else (phi - p0) / (p1 - p0)
    row0, row1 = grid_rt[i-1], grid_rt[i]
    return [ (1.0-w)*a + w*b for a,b in zip(row0,row1) ]

def _sign_index(lmb):
    return int((lmb % 360.0) // 30.0)

def _delta_oa_by_rt(rt12, lam1, lam2):
    if lam2 < lam1:
        lam2 += 360.0
    cur, end, s = lam1, lam2, 0.0
    while cur < end - 1e-12:
        si = _sign_index(cur)
        sign_end = (math.floor(cur/30.0)+1)*30.0
        step = min(sign_end, end) - cur
        s += rt12[si] * (step / 30.0)
        cur += step
    return s

def _term_edges_deg(options):
    """Return [(lam_start, lam_end, ruler_pid, sign_idx)] over 0..360°.

    - Morinus 옵션의 terms 구조가 환경에 따라
      * 각 텀의 '길이(span)' 5개 (합≈30) 이거나
      * 각 텀의 '끝도수(end)' 5개 (단조증가, 마지막≈30)
      로 들어오는 사례가 있어, 여기서 자동 판별한다.
    """
    edges = []
    sel = getattr(options, "selterm", 0)
    terms = options.terms[sel]    # [12][n][planet_id, value]

    lam0 = 0.0  # 각 사인의 시작 경도 0,30,60,…
    for sign in range(12):
        rows = terms[sign]
        # value 후보를 한 번에 뽑기
        vals = []
        pids = []
        for t in range(len(rows)):
            pid = rows[t][0]
            try:
                val = float(rows[t][1])
            except Exception:
                # (안전) 숫자가 아니면 0 취급
                val = 0.0
            pids.append(pid)
            vals.append(val)

        # --- 판별: span 형식인가 end 형식인가?
        use_span = False
        use_end  = False
        ssum = sum(vals)
        if 28.5 <= ssum <= 31.5:
            use_span = True
        # end 후보: 단조 증가 & 마지막이 28~30.5
        if all(vals[i] <= vals[i+1] for i in range(len(vals)-1)) and (28.0 <= vals[-1] <= 30.5):
            use_end = True

        # 애매하면 span 우선(실전에서 Morinus가 span인 빌드가 많음)
        mode = "span" if (use_span or not use_end) else "end"

        prev = 0.0
        if mode == "span":
            for t in range(len(vals)):
                span = max(0.0, min(vals[t], 30.0 - prev))
                a = lam0 + prev
                b = a + span
                if b - a > 1e-9:
                    edges.append((a, b, pids[t], sign))
                prev += span
        else:  # end
            for t in range(len(vals)):
                end = max(prev, min(vals[t], 30.0))
                a = lam0 + prev
                b = lam0 + end
                if b - a > 1e-9:
                    edges.append((a, b, pids[t], sign))
                prev = end

        lam0 += 30.0

    # 시작경도 기준 정렬 보장
    edges.sort(key=lambda x: x[0])
    return edges

def _planet_longitudes(chart_obj, options):
    pls = {}
    pmap = [
        (astrology.SE_SUN,  mtexts.txts.get('Sun','Sun')),
        (astrology.SE_MOON, mtexts.txts.get('Moon','Moon')),
        (astrology.SE_MERCURY, mtexts.txts.get('Mercury','Mercury')),
        (astrology.SE_VENUS,   mtexts.txts.get('Venus','Venus')),
        (astrology.SE_MARS,    mtexts.txts.get('Mars','Mars')),
        (astrology.SE_JUPITER, mtexts.txts.get('Jupiter','Jupiter')),
        (astrology.SE_SATURN,  mtexts.txts.get('Saturn','Saturn')),
    ]
    if options.transcendental[chart.Chart.TRANSURANUS]:
        pmap.append((astrology.SE_URANUS, mtexts.txts.get('Uranus','Uranus')))
    if options.transcendental[chart.Chart.TRANSNEPTUNE]:
        pmap.append((astrology.SE_NEPTUNE, mtexts.txts.get('Neptune','Neptune')))
    if options.transcendental[chart.Chart.TRANSPLUTO]:
        pmap.append((astrology.SE_PLUTO, mtexts.txts.get('Pluto','Pluto')))
    for pid, label in pmap:
        pls[label] = chart_obj.planets.planets[pid].data[0]
    return pls

def _exact_aspect_hits(lam_start_abs, lam_end_abs, planet_lams, aspects=(0,60,90,120,180)):
    """
    lam_start_abs, lam_end_abs : 절대 경도(증가 단조)
    planet_lams : {"Venus": 123.45, ...} (0..360)
    반환: [(L_abs, planet, A), ...]  -- 세그먼트 내부(양끝 제외)만
    """
    hits = []
    if lam_end_abs <= lam_start_abs + 1e-12:
        return hits

    for label, lp in planet_lams.items():
        lp = lp % 360.0
        for A in aspects:
            bases = [(lp - A) % 360.0]
            if A not in (0, 180):
                bases.append((lp + A) % 360.0)   # ±A 모두
            for base in bases:
                k_min = int(math.ceil((lam_start_abs - base) / 360.0))
                k_max = int(math.floor((lam_end_abs   - base) / 360.0))
                for k in range(k_min, k_max + 1):
                    L = base + 360.0 * k
                    if lam_start_abs + 1e-9 < L < lam_end_abs - 1e-9:  # 경계 제외
                        hits.append((L, label, A))
    hits.sort(key=lambda x: x[0])
    return hits

def _jd_add_years(jd0, years, calflag):
    return jd0 + years * DAYS_PER_YEAR

def calibrate_key_with_anchor(phi, lam_start, lam_end, observed_years):
    """Return key so that ΔOA(rt(phi), lam_start→lam_end) * key == observed_years."""
    rt12 = _interp_rt12(phi)
    doa  = _delta_oa_by_rt(rt12, lam_start%360.0, lam_end%360.0)
    if doa <= 0.0:
        return DEFAULT_KEY_Y_PER_DEG
    return float(observed_years) / doa
def _mean_obliquity_deg(jd):
    T = (jd - 2451545.0) / 36525.0
    eps = (84381.406
           - 46.836769*T
           - 0.0001831*T*T
           + 0.00200340*T**3
           - 5.76e-7*T**4
           - 4.34e-8*T**5) / 3600.0
    return eps
def compute_distributions(chrt, options, start_lambda=None, key=DEFAULT_KEY_Y_PER_DEG,
                          max_rows=200, include_participating=True, max_age_years=150):
    """
    Returns list of rows:
      - 'lam_start','lam_end','sign_idx','term_ruler_pid'
      - 'delta_oa','delta_years'
      - 'date_start','date_end'  (datetime.date)
      - 'participating' : [{'lam','planet','aspect','date'}, ...]
    """
    if start_lambda is None:
        start_lambda = chrt.houses.ascmc[houses.Houses.ASC]
    start_lambda = float(start_lambda) % 360.0

    phi = chrt.place.lat
    rt12 = _interp_rt12(phi)
    edges = _term_edges_deg(options)

    calflag = astrology.SE_GREG_CAL
    if chrt.time.cal == chart.Time.JULIAN:
        calflag = astrology.SE_JUL_CAL
    jd0 = astrology.swe_julday(chrt.time.year, chrt.time.month, chrt.time.day, chrt.time.time, calflag)
    # --- Polar guard: 고위도(극권)에서는 전통적 분배(OA/RT)가 물리적으로 미정의 ---
    # 임계 위도 = 90° - ε  (ε: 출생 시점의 황도경사)
    eps_deg   = _mean_obliquity_deg(jd0)
    phi_limit = 90.0 - eps_deg  # ≈ 66.56° 부근
    # 경계 근처의 수치 진동을 막기 위해 아주 소폭(0.01°) 안쪽에서 컷
    if abs(phi) >= (phi_limit - 0.01):
        raise ValueError(mtexts.txts['CircumPolarLatErr'].format(abs(phi), phi_limit))

    jd_limit = jd0 + max_age_years * DAYS_PER_YEAR

    rows = []
    planet_lams = _planet_longitudes(chrt, options) if include_participating else {}

    # 기존 ring 생성/탐색 블록 전체 삭제하고 ↓로 교체
    edges1 = _term_edges_deg(options)          # 이미 start로 정렬돼 있음
    start_mod = start_lambda % 360.0

    i0 = None
    for idx, (a, b, _, _) in enumerate(edges1):
        if (a - 1e-9) <= start_mod < (b - 1e-9):
            i0 = idx
            break
    if i0 is None:
        for idx, (a, b, _, _) in enumerate(edges1):
            if abs(start_mod - b) <= 1e-9:
                i0 = (idx + 1) % len(edges1)
                break
    if i0 is None:
        i0 = min(range(len(edges1)), key=lambda i: ((edges1[i][1] - start_mod) % 360.0))

    # 0..360° 구간을 a(시작경도) 기준으로 정렬
    edges1 = sorted(edges, key=lambda t: t[0])
    start_mod = start_lambda % 360.0

    # 포함 세그먼트 찾기 (우선)
    i0 = None
    for idx, (a, b, _, _) in enumerate(edges1):
        if (a - 1e-9) <= start_mod < (b - 1e-9):
            i0 = idx
            break
    # 경계선(==b)에 정확히 걸려 있으면 다음 세그먼트로
    if i0 is None:
        for idx, (a, b, _, _) in enumerate(edges1):
            if abs(start_mod - b) <= 1e-9:
                i0 = (idx + 1) % len(edges1)
                break
    # 그래도 못 찾으면: start_mod 이후 첫 b(없으면 0)
    if i0 is None:
        i0 = min(range(len(edges1)), key=lambda i: ((edges1[i][1] - start_mod) % 360.0))

    # 진행 루프 (edges1을 원형으로 순회)
    lam_cursor = start_lambda
    jd_cursor  = jd0
    idx = i0
    if jd_cursor >= jd_limit - 1e-9:
        return
        
    for _ in range(max_rows):
        a, b, pid, _sign_ignored = edges1[idx]
        seg_start = lam_cursor
        seg_end   = b

        delta_oa = _delta_oa_by_rt(rt12, seg_start, seg_end)
        if delta_oa <= 1e-9:
            lam_cursor = seg_end
            idx = (idx + 1) % len(edges1)
            continue
        delta_year = delta_oa * key
        jd_next    = _jd_add_years(jd_cursor, delta_year, calflag)

        # ★ rows.append에서 쓰일 시작/끝 날짜 + participatings를 먼저 계산
        y0, m0, d0, h0 = astrology.swe_revjul(jd_cursor, calflag)
        y1, m1, d1, h1 = astrology.swe_revjul(jd_next,   calflag)

        participants = []
        if include_participating and planet_lams:
            hits = _exact_aspect_hits(seg_start, seg_end, planet_lams)
            for L, label, A in hits:
                doa = _delta_oa_by_rt(rt12, seg_start, L)
                yrs = doa * key
                jd  = _jd_add_years(jd_cursor, yrs, calflag)
                if jd > jd_limit + 1e-9:
                    continue
                yy, mm, dd, hh = astrology.swe_revjul(jd, calflag)
                participants.append({
                    'lam':   L % 360.0,
                    'lam_abs': L,
                    'planet': label,
                    'aspect': A,
                    'doa':   doa,
                    'years': yrs,
                    'jd':    jd,
                    'date':  datetime.date(int(yy), int(mm), int(dd))
                })

        # ★ 150세 컷: 부분 구간으로 잘라 1줄 추가하고 종료
        if jd_next > jd_limit + 1e-9:
            remain_years = max(0.0, (jd_limit - jd_cursor) / DAYS_PER_YEAR)
            rem_doa = remain_years / max(key, 1e-12)

            sign_from_start = int(((seg_start % 360.0) // 30.0))
            rt_sign = rt12[sign_from_start]
            lam_end_cap = seg_start + (rem_doa / max(rt_sign, 1e-12)) * 30.0

            rows.append({
                'lam_start': seg_start % 360.0,
                'lam_end':   lam_end_cap % 360.0,
                'sign_idx':  sign_from_start,
                'term_ruler_pid': pid,
                'delta_oa':  rem_doa,
                'delta_years': remain_years,
                'date_start': datetime.date(int(y0), int(m0), int(d0)),
                'date_end':   datetime.date(int(y1), int(m1), int(d1)),  # y1은 jd_limit로 다시 계산해도 OK
                'jd_start':  jd_cursor,
                'jd_end':    jd_limit,
                'participating': participants
            })
            break

        else:
            # 정상 케이스: 한 텀 전체를 행으로 추가
            sign_from_start = int(((seg_start % 360.0) // 30.0))  # 0=Aries .. 11=Pisces
            rows.append({
                'lam_start': seg_start % 360.0,
                'lam_end':   seg_end   % 360.0,
                'sign_idx':  sign_from_start,
                'term_ruler_pid': pid,
                'delta_oa':  delta_oa,
                'delta_years': delta_year,
                'date_start': datetime.date(int(y0), int(m0), int(d0)),
                'date_end':   datetime.date(int(y1), int(m1), int(d1)),
                'jd_start':  jd_cursor,
                'jd_end':    jd_next,
                'participating': participants
            })

            # ★ 다음 세그먼트로 진행
            lam_cursor = seg_end
            jd_cursor  = jd_next
            idx = (idx + 1) % len(edges1)

    return rows

def planet_label(pid):
    base10 = [u"Sun", u"Moon", u"Mercury", u"Venus", u"Mars", u"Jupiter", u"Saturn",
              u"Uranus", u"Neptune", u"Pluto"]
    five   = [u"Mercury", u"Venus", u"Mars", u"Jupiter", u"Saturn"]
    try:
        x = int(pid)
    except Exception:
        return unicode(pid)
    if 0 <= x < len(base10):  # SwissEph 스타일
        return base10[x]
    if 0 <= x < 5:            # 5행성 전용
        return five[x]
    return unicode(pid)

