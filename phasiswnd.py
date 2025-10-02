# -*- coding: utf-8 -*-
# wx2.8 + Py2.7 + PIL 스타일 (fixed stars와 동일 톤)
import wx, datetime
import astrology
import common
import commonwnd
import Image, ImageDraw, ImageFont
import mtexts
from phasiscalc import (PLANET_IDS, PLANET_NAMES, visibility_flags_around,
                        is_outer)
import mtexts
# 라벨 매핑을 '지연 평가'로 바꾼다
def get_PHASE_LABELS():
    return {
        'MF': mtexts.txts['MorningFirst'],
        'ML': mtexts.txts['MorningLast'],
        'EF': mtexts.txts['EveningFirst'],
        'EL': mtexts.txts['EveningLast'],
    }

PHASIS_WINDOW_DAYS = 10
PHASIS_EMPTY       = u"—"

def get_PHASE_EMPTY_TIME():
    # Days 문구를 매번 현재 언어로 가져오게 한다
    return u"— (±%d %s)" % (PHASIS_WINDOW_DAYS, mtexts.txts['Days'])

def _fmt_day_offset(n):
    # n: int (dt - refdate).days
    sfx  = (u" " + (mtexts.txts['Day'] if abs(n) == 1 else mtexts.txts['Days']))
    sign = u"+" if n > 0 else (u"-" if n < 0 else u"")
    return u"%s%d%s" % (sign, abs(n), sfx)

def _extract_chart_ymd(chart):
    """
    chart.time 안에서 연/월/일 필드를 최대한 호환성 있게 추출한다.
    못 찾으면 None 반환.
    """
    if not hasattr(chart, 'time'):
        return None
    t = chart.time
    def pick(obj, names):
        for nm in names:
            if hasattr(obj, nm):
                v = getattr(obj, nm)
                if isinstance(v, (int, long)) or (isinstance(v, basestring) and unicode(v).strip()):
                    try:
                        return int(v)
                    except:
                        pass
        return None

    y = pick(t, ('y','year','yyyy','yr','jy','iy'))   # 빌드마다 이름 다를 수 있음
    m = pick(t, ('m','month','mon'))                  # mon/ month
    d = pick(t, ('d','day','dom'))                    # day/ dom
    if y is None or m is None or d is None:
        return None
    return (y, m, d)

def _get_cal_flag(chart, options, jd0):
    """
    1) chart.time에 저장된 '원래 입력한 Y/M/D'와
       swe_revjul(jd0, JUL/GREG) 결과를 직접 대조해서 확정.
    2) (백업) chart/options의 여러 후보 필드명에서 플래그 읽기.
    3) (최종) 그래도 실패하면 Gregorian.
    """
    # 1) 직접 대조 (가장 신뢰도 높음)
    try:
        ymd_in = _extract_chart_ymd(chart)
        if ymd_in is not None:
            yJ, mJ, dJ, _ = astrology.swe_revjul(jd0, astrology.SE_JUL_CAL)
            yG, mG, dG, _ = astrology.swe_revjul(jd0, astrology.SE_GREG_CAL)
            if (yJ, mJ, dJ) == ymd_in:
                return astrology.SE_JUL_CAL
            if (yG, mG, dG) == ymd_in:
                return astrology.SE_GREG_CAL
    except:
        pass

    # 2) 필드에서 읽기(기존 방식, 이름 풀 강화)
    def _read_flag(obj, names):
        for nm in names:
            if hasattr(obj, nm):
                v = getattr(obj, nm)
                if isinstance(v, bool):
                    return astrology.SE_GREG_CAL if v else astrology.SE_JUL_CAL
                if v in (0, 1, astrology.SE_JUL_CAL, astrology.SE_GREG_CAL):
                    return int(v)
        return None

    if hasattr(chart, 'time'):
        v = _read_flag(chart.time, ('cal','calendar','calflag','gregflag','gregorian'))
        if v is not None:
            return v
    if options is not None:
        v = _read_flag(options, ('cal','calendar','calflag','gregflag','gregorian'))
        if v is not None:
            return v

    # 3) 마지막 안전망
    return astrology.SE_GREG_CAL

USE_ASTRONOMICAL_YEAR = False  # Radix 스타일(음수연도)로 맞추고 싶으면 True

def _fmt_astro_date(y, m, d):
    try:
        y = int(y); m = int(m); d = int(d)
    except:
        return u"—"

    if y > 0:
        # 서기(연도 1~)
        return u"%04d.%02d.%02d" % (y, m, d)

    if USE_ASTRONOMICAL_YEAR:
        # Radix와 완전히 동일한 스타일(음수 연도 표기)
        return u"-%04d.%02d.%02d" % (abs(y), m, d)

    # 역사적 BC 표기(연도 0 없음): y=0→1 BC, y=-1→2 BC, y=-1633→1634 BC
    bce = 1 - y            # ★ 핵심: -y가 아니라 1 - y
    return u"%04d.%02d.%02d BC" % (bce, m, d)

class PhasisWnd(commonwnd.CommonWnd):
    """
    fixed stars/antiscia/firdaria와 동일한 CommonWnd + PIL 파이프라인.
    왼쪽 첫 칸은 행성 '기호(글리프)'로 표시.
    """

    def __init__(self, parent, horoscope, options, mainfr, id=-1, size=wx.DefaultSize):
        commonwnd.CommonWnd.__init__(self, parent, horoscope, options, id, size)

        # 레퍼런스
        self.parent    = parent
        self.chart     = horoscope
        self.options   = options
        self.mainfr    = mainfr
        self.bw        = self.options.bw

        # ======== fixed stars 규격 준용 (폰트/여백/선두께) ========

        # ① 글꼴/크기 (테이블 전역 스케일은 tablesize로)
        self.FONT_SIZE    = int(21 * self.options.tablesize)   # 글자 크기
        self.SPACE        = self.FONT_SIZE / 2                 # 위/아래 여백
        self.LINE_HEIGHT  = (self.SPACE + self.FONT_SIZE + self.SPACE)
        # PATCH: info 영역을 2행으로 (세로줄 없음)
        self.INFO_HEIGHT  = self.LINE_HEIGHT
        self.INFO_ROWS    = 1
        self.INFO_BLOCK_H = int(self.INFO_ROWS * self.INFO_HEIGHT)
        # ② 컬럼 폭 (왼쪽 기호 칸은 좁게)
        #    [Planet(기호), Phasis, Time]
        self.W_SYM   = 5 * self.FONT_SIZE        # 기호 칸 (antiscia/firdaria SMALL_CELL_WIDTH에 맞춤)
        self.W_PHAS  = 8 * self.FONT_SIZE        # 라벨 칸
        self.W_TIME  = 12 * self.FONT_SIZE       # 시간 칸
        self.TITLE_HEIGHT = self.LINE_HEIGHT
        self.TITLE_WIDTH  = (self.W_SYM + self.W_PHAS + self.W_TIME)

        # ③ 폰트 로드 (심볼/텍스트)
        self.fntMorinus = ImageFont.truetype(common.common.symbols, self.FONT_SIZE)  # 행성 기호
        self.fntText    = ImageFont.truetype(common.common.abc,     self.FONT_SIZE)  # 일반 텍스트

        # ④ 행 수 및 버퍼 크기 계산
        self.rows = self._compute_rows()     # 각 행: (ipl, symbol, phasis_text, time_text, color)
        self.LINE_NUM = len(self.rows)       # 모든 행성 표시(빈칸 대신 '—' 사용, 빈행 만들지 않음)
        self.TABLE_HEIGHT = int(self.INFO_BLOCK_H + self.TITLE_HEIGHT + self.LINE_NUM * self.LINE_HEIGHT)

        BOR = commonwnd.CommonWnd.BORDER
        self.WIDTH  = int(BOR + self.TITLE_WIDTH  + BOR)
        self.HEIGHT = int(BOR + self.TABLE_HEIGHT + BOR)
        self.SetVirtualSize((self.WIDTH, self.HEIGHT))

        self.drawBkg()
    # 클래스 내부 어딘가(예: drawBkg 위)에 추가
    def _get_extinction_and_altitude(self):
        """
        phasiscalc.visibility_flags_around()가 돌려준 vis 딕셔너리에서
        AE(= kV_from_altitude)와 관측지 고도(m)를 가져온다.
        - AE가 없으면(이상 케이스) 마지막 안전망으로 kV_from_altitude(alt) 계산.
        """
        # 고도
        try:
            alt = float(getattr(self, '_alt_m', None) if hasattr(self, '_alt_m') else self.chart.place.altitude)
        except Exception:
            alt = 0.0

        # AE 꺼내기(모든 행성에 동일 값이 들어가 있으므로 첫 유효값 사용)
        k = None
        try:
            vis = getattr(self, '_vis', None)
            if isinstance(vis, dict):
                for ipl in PLANET_IDS:
                    if ipl in vis and 'AE' in vis[ipl]:
                        k = float(vis[ipl]['AE'])
                        break
        except Exception:
            k = None

        # 안전망: AE가 못 나왔으면 고도 기반으로 직접 계산
        if k is None:
            try:
                from phasiscalc import kV_from_altitude
                k = float(kV_from_altitude(alt))
            except Exception:
                k = 0.0

        return k, alt
    # ------------------------------------------------------------
    # 저장 시 파일명 접미사
    def getExt(self):
        try:
            return mtexts.txts['Phasis']
        except:
            return u"Phasis"

    # ------------------------------------------------------------
    # 내부: 데이터 계산 (기존 ListCtrl 버전의 로직을 그대로 재현)
    def _compute_rows(self):
        rows = []
        vis = visibility_flags_around(self.chart, days_window=PHASIS_WINDOW_DAYS)
        self._vis = vis
        try:
            self._alt_m = float(self.chart.place.altitude)
        except Exception:
            self._alt_m = 0.0
        order = PLANET_IDS

        # 참조 기준일 (정오/자정 보정 없이 달력 날짜만 사용)
        jd0 = self.chart.time.jd
        calflag = _get_cal_flag(self.chart, self.options, jd0)
        y0, m0, d0, _ = astrology.swe_revjul(jd0, calflag)

        # 라벨 우선순위 (가까운 날짜가 1순위, 동률 시 이 순으로 선택)
        pref = {'MF':0, 'ML':1, 'EF':2, 'EL':3}

        for ipl in order:
            # 1) 심볼
            plist = common.common.Planets
            sym = plist[min(ipl, len(plist)-1)]

            # 2) 이벤트 후보 수집 (±PHASIS_WINDOW_DAYS)
            events = []  # (code, (y,m,d), off)
            codes = ('EL', 'MF') if is_outer(ipl) else ('MF', 'ML', 'EF', 'EL')
            off_map = vis.get(ipl, {}) or {}
            for code in codes:
                off = off_map.get(code, None)
                if isinstance(off, int) and abs(off) <= PHASIS_WINDOW_DAYS:
                    y, m, d, _ = astrology.swe_revjul(jd0 + off, calflag)
                    events.append((code, (y, m, d), off))

            # 3) 결과 문자열 구성
            if events:
                # 오프셋 절대값이 가장 작은 것, 동률이면 코드 우선순위
                best = sorted(events, key=lambda t: (abs(t[2]), pref[t[0]]))[0]
                lbl, (yy, mm, dd), off = best
                phasis_txt = get_PHASE_LABELS().get(lbl, lbl)
                offs_txt   = _fmt_day_offset(off)
                date_txt   = _fmt_astro_date(yy, mm, dd)
                time_txt   = u"%s (%s)" % (date_txt, offs_txt)
            else:
                phasis_txt = PHASIS_EMPTY
                time_txt   = get_PHASE_EMPTY_TIME()

            # 4) 기호 색: fixed stars 계열 규칙 (useplanetcolors↓ / dignity 색상↑)
            clr = (0, 0, 0)  # BW/기본
            if not self.bw:
                objidx = ipl
                if self.options.useplanetcolors:
                    # 인덱스 범위 보정
                    objidx = min(objidx, len(self.options.clrindividual)-1)
                    clr = self.options.clrindividual[objidx]
                else:
                    # 존비 dignities 기반 색
                    try:
                        dign = self.chart.dignity(ipl)
                    except:
                        dign = 0
                    pal = [self.options.clrdomicil, self.options.clrexal,
                           self.options.clrperegrin, self.options.clrcasus,
                           self.options.clrexil]
                    clr = pal[dign if 0 <= dign < len(pal) else 0]

            rows.append((ipl, sym, phasis_txt, time_txt, clr))
        return rows

    # ------------------------------------------------------------
    # 렌더: 헤더/세로선/가로선/텍스트 모두 PIL로 직접 그리기
    def drawBkg(self):
        # 색/배경
        self.bkgclr = (255,255,255) if self.bw else self.options.clrbackground
        self.SetBackgroundColour(self.bkgclr)
        tableclr = (0,0,0) if self.bw else self.options.clrtable
        txtclr   = (0,0,0) if self.bw else self.options.clrtexts

        BOR = commonwnd.CommonWnd.BORDER
        img  = Image.new('RGB', (self.WIDTH, self.HEIGHT), self.bkgclr)
        draw = ImageDraw.Draw(img)

        # --- [A] info 2행 (세로줄 없음, 중앙정렬) ---
        txt_info1 = (mtexts.txts["HeliacalRisingsSettings"]+ u"\u00B1%d " + mtexts.txts["Days"]) % (PHASIS_WINDOW_DAYS,)

        info_x = BOR
        info_w = self.TITLE_WIDTH
        row_h  = self.INFO_HEIGHT  # ← 오타 고친 부분

        # 1행
        w1, h1 = draw.textsize(txt_info1, self.fntText)
        draw.text((info_x + (info_w - w1)/2, BOR + (row_h - h1)/2),
                txt_info1, fill=txtclr, font=self.fntText)

        # --- [B] 헤더(Planet/Phasis/Time) ---
        head_y = BOR + self.INFO_BLOCK_H  # ← info 2행 아래
        draw.rectangle(((BOR, head_y), (BOR + self.TITLE_WIDTH, head_y + self.TITLE_HEIGHT)),
                    outline=tableclr, fill=self.bkgclr)
        heads = (mtexts.txts["Planets"], mtexts.txts["Phasis"], mtexts.txts["TimeDays"])
        col_w = (self.W_SYM, self.W_PHAS, self.W_TIME)
        x = BOR
        for i, htxt in enumerate(heads):
            tw, th = draw.textsize(htxt, self.fntText)
            draw.text((x + (col_w[i]-tw)/2, head_y + (self.TITLE_HEIGHT - th)/2),
                    htxt, fill=txtclr, font=self.fntText)
            x += col_w[i]

        # 헤더 하단선
        x0 = BOR
        y0 = head_y + self.TITLE_HEIGHT
        draw.line((x0, y0, x0 + self.TITLE_WIDTH, y0), fill=tableclr)

        # --- [C] 세로 구분선: 헤더 상단부터 표 끝까지 ---
        top_of_cols = BOR + self.INFO_BLOCK_H
        table_h     = self.TABLE_HEIGHT
        xv = x0
        draw.line((xv, top_of_cols, xv, BOR + table_h), fill=tableclr)  # 왼쪽 외곽
        for w in col_w:
            xv += w
            draw.line((xv, top_of_cols, xv, BOR + table_h), fill=tableclr)

        # --- [D] 데이터 행 ---
        y = y0
        for (ipl, sym, phasis_txt, time_txt, clr) in self.rows:
            draw.line((x0, y + self.LINE_HEIGHT, x0 + self.TITLE_WIDTH, y + self.LINE_HEIGHT), fill=tableclr)

            # Planet 기호
            tw, th = draw.textsize(sym, self.fntMorinus)
            draw.text((x0 + (self.W_SYM - tw)/2, y + (self.LINE_HEIGHT - th)/2),
                    sym, fill=clr, font=self.fntMorinus)

            # Phasis
            cx = x0 + self.W_SYM
            tw, th = draw.textsize(phasis_txt, self.fntText)
            draw.text((cx + (self.W_PHAS - tw)/2, y + (self.LINE_HEIGHT - th)/2),
                    phasis_txt, fill=txtclr, font=self.fntText)

            # Time
            cx += self.W_PHAS
            tw, th = draw.textsize(time_txt, self.fntText)
            draw.text((cx + (self.W_TIME - tw)/2, y + (self.LINE_HEIGHT - th)/2),
                    time_txt, fill=txtclr, font=self.fntText)

            y += self.LINE_HEIGHT

        # --- [E] 전체 외곽 테두리 ---
        draw.rectangle(((BOR, BOR), (BOR + self.TITLE_WIDTH, BOR + self.TABLE_HEIGHT)), outline=tableclr)

        # wx로 전송
        wxImg = wx.Image(img.size[0], img.size[1])
        wxImg.SetData(img.tobytes())
        self.buffer = wx.Bitmap(wxImg)
        self.Refresh()
