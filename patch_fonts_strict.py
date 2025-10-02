# -*- coding: utf-8 -*-
# Robust vertical-metrics patcher for TTF (glyf/CFF 모두 지원)
from __future__ import print_function
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
import os, math

FONTS = ["Res/DejaVuSansCondensed.ttf", "Res/Morinus.ttf"]

# 안전 여유: upm의 8% (너무 타이트하면 0.10~0.12로 올리세요)
LINEGAP_RATIO = 0.12
FUDGE_RATIO   = 0.12  # head/OS2/hhea에 추가로 얹을 여유

def compute_true_bbox(tt):
    """모든 글리프를 실제로 그려서 (xMin,yMin,xMax,yMax) 반환"""
    gset = tt.getGlyphSet()
    pen  = BoundsPen(gset)
    yMin = +10**9
    yMax = -10**9
    for name in gset.keys():
        pen.init()
        try:
            gset[name].draw(pen)
        except Exception:
            continue
        if pen.bounds:
            x0, y0, x1, y1 = pen.bounds
            if y0 is not None and y1 is not None:
                yMin = min(yMin, int(math.floor(y0)))
                yMax = max(yMax, int(math.ceil(y1)))
    if yMin > yMax:
        # 폴백: 기존 head
        yMin = tt["head"].yMin
        yMax = tt["head"].yMax
    return yMin, yMax

def patch(path):
    tt = TTFont(path)
    head = tt["head"]
    upm  = head.unitsPerEm

    # 1) 실제 글리프 기준 global bbox 재계산
    realYMin, realYMax = compute_true_bbox(tt)
    fudge = int(round(upm * FUDGE_RATIO))
    gap   = int(round(upm * LINEGAP_RATIO))

    newYMin = min(head.yMin, realYMin) - fudge
    newYMax = max(head.yMax, realYMax) + fudge

    # 2) head (전역 BBox) 확장
    head.yMin = newYMin
    head.yMax = newYMax

    # 3) OS/2 테이블 (Win/Typo 라인박스 모두 확장 + UseTypoMetrics on)
    if "OS/2" in tt:
        os2 = tt["OS/2"]
        os2.usWinAscent  = max(getattr(os2, "usWinAscent", 0),  newYMax)
        os2.usWinDescent = max(getattr(os2, "usWinDescent", 0), -newYMin)

        # Typo metrics는 라인박스(문단 박스)가 넉넉해야 잘림이 사라짐
        os2.sTypoAscender  = max(getattr(os2, "sTypoAscender", 0),  newYMax)
        os2.sTypoDescender = min(getattr(os2, "sTypoDescender", 0), newYMin)
        os2.sTypoLineGap   = max(getattr(os2, "sTypoLineGap", 0),   gap)

        # UseTypoMetrics 비트 on (fsSelection bit 7)
        os2.fsSelection = os2.fsSelection | (1 << 7)

    # 4) hhea 테이블 (일부 렌더러는 이걸 따름)
    if "hhea" in tt:
        hhea = tt["hhea"]
        hhea.ascent  = max(hhea.ascent,  newYMax)
        hhea.descent = min(hhea.descent, newYMin)
        hhea.lineGap = max(hhea.lineGap, gap)

    out = path.replace(".ttf", "_patched2.ttf")
    tt.save(out)
    print("patched:", out,
          "  (yMin=%d, yMax=%d, gap=%d)" % (newYMin, newYMax, gap))

if __name__ == "__main__":
    base = os.path.dirname(__file__) or "."
    os.chdir(base)
    for p in FONTS:
        if os.path.exists(p):
            patch(p)
        else:
            print("not found:", p)
