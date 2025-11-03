# -*- coding: utf-8 -*-
"""
Decennials (10 years 9 months per planet) — L1/L2 only, A-scheme (30-day schematic month).
- L1: 129 months × 30 days = 3,870 days per planet
- L2: minor-years months × 30 days inside L1, starting from the L1 planet
  Saturn 30, Jupiter 12, Mars 15, Sun 19, Venus 8, Mercury 20, Moon 25 (months)
Ordering:
- Start from sect light (Sun by day, Moon by night), then proceed by zodiacal order of the seven planets’
  ecliptic longitudes at birth (wrapping 360°).
"""
import datetime
import astrology, planets, util
import astrology, planets, util, houses, fortune

MINOR_MONTHS = {
    astrology.SE_SATURN: 30,
    astrology.SE_JUPITER: 12,
    astrology.SE_MARS:    15,
    astrology.SE_SUN:     19,
    astrology.SE_VENUS:    8,
    astrology.SE_MERCURY: 20,
    astrology.SE_MOON:    25,
}

SCHEMATIC_DAY   = 1.0
SCHEMATIC_MONTH = 30 * SCHEMATIC_DAY
L1_MONTHS = 129
L1_DAYS   = L1_MONTHS * SCHEMATIC_MONTH
MINOR_TOTAL = 129.0  # 발렌스식 재분배 계수(소년수 합계)

def _chart_datetime(chart):
    # 시작 시각은 "원본 현지 입력" 기준으로 고정 (UTC 변환 금지)
    t = chart.time
    y  = int(getattr(t, 'origyear',  getattr(t, 'year')))
    m  = int(getattr(t, 'origmonth', getattr(t, 'month')))
    d  = int(getattr(t, 'origday',   getattr(t, 'day')))
    hh = int(getattr(t, 'hour',    0))
    mi = int(getattr(t, 'minute',  0))
    ss = int(getattr(t, 'second',  0))
    return datetime.datetime(y, m, d, hh, mi, ss)

def _seven_classicals():
    return [astrology.SE_SATURN, astrology.SE_JUPITER, astrology.SE_MARS,
            astrology.SE_SUN, astrology.SE_VENUS, astrology.SE_MERCURY, astrology.SE_MOON]

def _is_diurnal(chart):
    try:
        return bool(chart.isAboveHorizonWithOrb())
    except Exception:
        return True

def _planet_order(chart, options):
    pairs = []
    for p in _seven_classicals():
        lon = chart.planets.planets[p].data[planets.Planet.LONG]
        if options.ayanamsha != 0:
            lon = util.normalize(lon - chart.ayanamsha)
        pairs.append((p, lon))
    pairs.sort(key=lambda x: x[1])
    start = astrology.SE_SUN if _is_diurnal(chart) else astrology.SE_MOON
    idx = 0
    for i,(pp,_) in enumerate(pairs):
        if pp == start:
            idx = i; break
    order = [pairs[(idx+i) % 7][0] for i in range(7)]
    return order

def _planet_order_raw(chart, options):
    """황도경도 오름차순 정렬(회전 없음). 반환: [행성se_index..]"""
    pairs = []
    for p in _seven_classicals():
        lon = chart.planets.planets[p].data[planets.Planet.LONG]
        if options.ayanamsha != 0:
            lon = util.normalize(lon - chart.ayanamsha)
        pairs.append((p, lon))
    pairs.sort(key=lambda x: x[1])
    return [pp for (pp, _) in pairs]

def _planet_after_degree(chart, options, deg):
    """deg 이후 최초로 나타나는 행성을 반환(없으면 첫 원소)."""
    pairs = []
    for p in _seven_classicals():
        lon = chart.planets.planets[p].data[planets.Planet.LONG]
        if options.ayanamsha != 0:
            lon = util.normalize(lon - chart.ayanamsha)
        pairs.append((p, lon))
    pairs.sort(key=lambda x: x[1])
    for (pp, lon) in pairs:
        if lon >= deg:
            return pp
    return pairs[0][0]

def _resolve_start_planet(chart, options, selector):
    """
    selector: 'sect' | 'sun'|'moon'|'mercury'|'venus'|'mars'|'jupiter'|'saturn'
              | 'asc' | 'fortune'
    반환: astrology.SE_* 정수 (행성)
    """
    s = (selector or 'sect').strip().lower()
    # 1) 섹트
    if s == 'sect':
        return astrology.SE_SUN if _is_diurnal(chart) else astrology.SE_MOON
    # 2) 행성 지정
    pmap = {
        'sun': astrology.SE_SUN, 'moon': astrology.SE_MOON,
        'mercury': astrology.SE_MERCURY, 'venus': astrology.SE_VENUS,
        'mars': astrology.SE_MARS, 'jupiter': astrology.SE_JUPITER,
        'saturn': astrology.SE_SATURN
    }
    if s in pmap:
        return pmap[s]
    # 3) 감응점: ASC, 로트 오브 포츈 → 해당 경도 바로 뒤의 첫 행성
    if s == 'asc':
        deg = chart.houses.ascmc2[houses.Houses.ASC][houses.Houses.LON]
        return _planet_after_degree(chart, options, deg)
    if s == 'fortune':
        deg = chart.fortune.fortune[fortune.Fortune.LON]
        return _planet_after_degree(chart, options, deg)
    # 안전 폴백
    return astrology.SE_SUN if _is_diurnal(chart) else astrology.SE_MOON

def _dur_days(level, planet):
    if level == 1:
        return L1_DAYS
    if level == 2:
        return MINOR_MONTHS[planet] * SCHEMATIC_MONTH
    raise ValueError("Unsupported level")

def build_main(chart, options, cycles=2, start_selector='sect'):
    """
    Return interleaved L1/L2 rows for given cycles (default 2).
    Each row: {'level': 1|2, 'planet': se_index, 'start': datetime, 'end': datetime}
    """
    out = []
    t = _chart_datetime(chart)
    order = _planet_order(chart, options)
    startp = _resolve_start_planet(chart, options, start_selector)
    order = order[order.index(startp):] + order[:order.index(startp)]
    for c in range(int(cycles)):
        for p in order:
            s = t
            e = s + datetime.timedelta(days=_dur_days(1, p))
            out.append({'level': 1, 'planet': p, 'start': s, 'end': e})
            # L2 stream (order rotated to start from L1 planet)
            idx0 = order.index(p)
            sub_order = order[idx0:] + order[:idx0]
            tt = s
            for sp in sub_order:
                ss = tt
                ee = ss + datetime.timedelta(days=_dur_days(2, sp))
                if ee > e: ee = e
                out.append({'level': 2, 'planet': sp, 'start': ss, 'end': ee})
                tt = ee
            t = e
    return out
def build_children_valens(chart, options, parent_row, level):
    """
    발렌스식: 하위 단계 길이는 상위 구간 길이에 7행성 '소년수 비율(=minor_months/129)'을 곱해 재분배.
    parent_row: L2(→L3 생성) 또는 L3(→L4 생성)
    반환 Each row: {'level': 3|4, 'planet': se_index, 'start': dt, 'end': dt}
    """
    if level not in (3, 4):
        raise ValueError("level must be 3 or 4")

    order = _planet_order(chart, options)
    # 하위 단계도 항상 '부모 행성'에서 시작하도록 순서를 회전
    startp = int(parent_row['planet'])
    i0 = order.index(startp)
    sub_order = order[i0:] + order[:i0]

    base_days = (parent_row['end'] - parent_row['start']).total_seconds() / 86400.0
    t = parent_row['start']
    out = []
    acc = 0.0
    for j, sp in enumerate(sub_order):
        # 비율배분: (소년수 / 129) × 부모 길이(일)
        seg_days = base_days * (MINOR_MONTHS[sp] / MINOR_TOTAL)
        ss = t
        ee = ss + datetime.timedelta(days=seg_days)
        out.append({'level': level, 'planet': sp, 'start': ss, 'end': ee})
        t = ee
        acc += seg_days
    # 누적 오차 보정: 마지막 세그먼트의 끝을 부모 끝에 강제 일치
    out[-1]['end'] = parent_row['end']
    return out
def build_children_combo_valens(chart, options, parent_row):
    """
    L2 한 구간을 받아서: L3 전 구간을 만들고, 각 L3 안에 L4를 시간 순서로 바로 이어붙여
    하나의 납작한 목록으로 반환한다. (정렬은 시간 흐름 그대로)
    """
    out = []
    rows3 = build_children_valens(chart, options, parent_row, level=3)
    for r3 in rows3:
        out.append(r3)
        rows4 = build_children_valens(chart, options, r3, level=4)
        out.extend(rows4)
    return out

# Formatting helpers (same style as zodiacalreleasing)
try:
    import mtexts
except Exception:
    mtexts = None

def fmt_date(dt):
    return u'%04d.%02d.%02d' % (int(dt.year), int(dt.month), int(dt.day))

def fmt_length(row):
    td = row['end'] - row['start']
    days = td.total_seconds() / 86400.0
    if row['level'] == 1:
        yrs = days / 360.0
        unit = mtexts.txts['Year'] if abs(yrs) == 1 else mtexts.txts['Years']
        return u'%.0f %s' % (yrs, unit)
    if row['level'] == 2:
        months = int(round(days / 30.0))
        unit = mtexts.txts['Month'] if abs(months) == 1 else mtexts.txts['Months']
        return u'%d %s' % (months, unit)
    # L3/L4: 소수 월이 너무 작아 0으로 떨어지므로 '일'로 표기
    d = int(round(days))
    unit = mtexts.txts['Day'] if abs(d) == 1 else mtexts.txts['Days']
    return u'%d %s' % (d, unit)
