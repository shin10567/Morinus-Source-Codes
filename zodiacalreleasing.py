# -*- coding: utf-8 -*-
"""
Zodiacal releasing calculator (Python 2.7, wxClassic)
- Weights: Aries15, Taurus8, Gemini20, Cancer25, Leo19, Virgo20, Libra8, Scorpio15, Sagittarius12, Capricorn27, Aquarius30, Pisces12
- Level base units:
  L1 = 360 days  × weight
  L2 = 30  days  × weight
  L3 = 2.5 days  × weight   (== 60 hours × weight)
  L4 = 5   hours × weight
- Loosing of the Bond (LoB) on L2/L3/L4:
  Each sublevel starts from parent_start_sign and proceeds in zodiacal order;
  at the first moment it would re-enter the parent_start_sign, jump to its opposite,
  then continue naturally from there (one-time jump per chain). Durations are unchanged.
"""
from __future__ import division
import datetime
import mtexts

# 0..11 = Aries..Pisces
SIGN_NAMES = [mtexts.txts['Aries'], mtexts.txts['Taurus'], mtexts.txts['Gemini'], mtexts.txts['Cancer'], mtexts.txts['Leo'], mtexts.txts['Virgo'],
              mtexts.txts['Libra'], mtexts.txts['Scorpio'], mtexts.txts['Sagittarius'], mtexts.txts['Capricornus'], mtexts.txts['Aquarius'], mtexts.txts['Pisces']]

WEIGHTS = [15, 8, 20, 25, 19, 20, 8, 15, 12, 27, 30, 12]

L1_BASE_DAYS = 360.0
L2_BASE_DAYS = 30.0
L3_BASE_HRS  = 60.0   # 2.5 days
L4_BASE_HRS  = 5.0

def next_sign(i): return (i + 1) % 12
def opp(i): return (i + 6) % 12

def _dur(level, sign_idx):
    w = WEIGHTS[sign_idx]
    if level == 1:
        return datetime.timedelta(days=L1_BASE_DAYS * w)
    if level == 2:
        return datetime.timedelta(days=L2_BASE_DAYS * w)
    if level == 3:
        return datetime.timedelta(hours=L3_BASE_HRS * w)
    # level == 4
    return datetime.timedelta(hours=L4_BASE_HRS * w)

def _stream_sublevel(parent_start, parent_end, parent_start_sign, level):
    """
    Generate L(level) rows inside [parent_start, parent_end].
    LoB: one-time jump when next sign would be parent_start_sign.
    Rows may be truncated at parent_end.
    """
    rows = []
    t = parent_start
    sgn = parent_start_sign
    lob_done = False

    while t < parent_end:
        dur = _dur(level, sgn)
        e = t + dur
        if e > parent_end:
            e = parent_end

        rows.append({'level': level, 'sign': sgn, 'start': t, 'end': e})

        # advance time and sign
        t = e
        nxt = next_sign(sgn)
        if (not lob_done) and nxt == parent_start_sign:
            sgn = opp(parent_start_sign)
            lob_done = True
        else:
            sgn = nxt

        # guard against zero-advance due to extreme truncation
        if t >= parent_end:
            break
    return rows

def build_main(start_dt, start_sign_idx, years_horizon=120):
    """
    Build main table rows: interleaved L1 + L2 (L2 within each L1 interval).
    Returns a list of rows with 'level' in {1,2}.
    """
    out = []
    # L1 stream across horizon
    t = start_dt
    sgn = start_sign_idx
    acc_years = 0.0
    while acc_years < years_horizon:
        dur = _dur(1, sgn)
        s = t
        e = t + dur
        out.append({'level': 1, 'sign': sgn, 'start': s, 'end': e})
        # L2 inside this L1
        l2_rows = _stream_sublevel(s, e, sgn, level=2)
        out.extend(l2_rows)
        # advance
        t = e
        acc_years += WEIGHTS[sgn]
        sgn = next_sign(sgn)
    return out

def build_drill(parent_row):
    """
    For popup: given an L2 row dict, compute L3 + L4 inside it.
    Returns (l3_rows, l4_rows).
    """
    s = parent_row['start']
    e = parent_row['end']
    parent_start_sign = parent_row['sign']
    l3 = _stream_sublevel(s, e, parent_start_sign, level=3)
    # chain L4 inside each L3
    l4 = []
    for r in l3:
        l4.extend(_stream_sublevel(r['start'], r['end'], r['sign'], level=4))
    return (l3, l4)

def fmt_length(row):
    td = row['end'] - row['start']
    secs = td.total_seconds()
    days = secs / 86400.0

    if row['level'] == 1:
        yrs = days / 360.0
        unit = mtexts.txts['Year'] if abs(yrs) == 1 else mtexts.txts['Years']
        return u'%.0f %s' % (yrs, unit)

    if row['level'] == 2:
        total_days = int(round(days))
        months = total_days // 30
        unit = mtexts.txts['Month'] if abs(months) == 1 else mtexts.txts['Months']
        return u'%d %s' % (months, unit)

    if row['level'] in (3, 4):
        unit = mtexts.txts['Day'] if abs(days) == 1 else mtexts.txts['Days']
        return u"%.1f %s" % (days, unit)

def fmt_date(dt):
    # strftime은 year<1900에서 ValueError를 내므로 수동 포맷
    return u'%04d.%02d.%02d' % (int(dt.year), int(dt.month), int(dt.day))
