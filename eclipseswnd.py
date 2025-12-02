# -*- coding: utf-8 -*-
import wx
import os
from PIL import Image, ImageDraw, ImageFont
import mtexts
import common
import commonwnd
import util
import astrology
import eclipses
import math

class EclipsesWnd(commonwnd.CommonWnd):
    # 셀/폰트/간격 값은 기존 표들과 동일 계열
    LINE_HEIGHT = 24
    CELL_WIDTH  = 160
    SMALL_CELL_WIDTH = 28
    BIG_CELL_WIDTH   = 180
    TITLE_HEIGHT = 28
    SPACE_TITLEY = 6
    FONT_SIZE    = 12

    def __init__(self, parent, chrt, options, mainfr=None, id = -1, size = wx.DefaultSize):
        commonwnd.CommonWnd.__init__(self, parent, chrt, options, id, size)
        self.mainfr = mainfr
        self.deg_symbol = u'\u00b0'  # positionswnd와 동일

        # positionswnd와 같은 규칙(표 크기 = tablesize 기반)
        self.FONT_SIZE = int(21*self.options.tablesize)
        self.SPACE = self.FONT_SIZE//2
        self.LINE_HEIGHT = self.SPACE + self.FONT_SIZE + self.SPACE
        self.SMALL_CELL_WIDTH = 3*self.FONT_SIZE
        self.CELL_WIDTH = 10*self.FONT_SIZE
        self.TITLE_HEIGHT = self.LINE_HEIGHT
        self.SPACE_TITLEY = 0

        # 폰트/기호
        self.fntMorinus = ImageFont.truetype(common.common.symbols, int(self.FONT_SIZE))
        # UI 기본 텍스트 폰트 (다국어용)
        self.fntText    = ImageFont.truetype(common.common.abc, int(self.FONT_SIZE))
        try:
            # 조디악 릴리징과 동일하게 abc_bold 사용 (실제 Bold TTF)
            self.fntTextBold = ImageFont.truetype(common.common.abc_bold, int(self.FONT_SIZE))
        except Exception:
            # abc_bold 없으면 일반 폰트로 폴백
            self.fntTextBold = self.fntText

        # ----------------------------------------------------------
        # 경도/도데카 숫자용 영어폰트
        #   - 기본: abc_ascii (없으면 UI 폰트)
        #   - Bold: res/freesansbold.ttf 를 최우선 사용
        # ----------------------------------------------------------
        try:
            self.fntAscii = ImageFont.truetype(common.common.abc_ascii, int(self.FONT_SIZE))
        except Exception:
            # 없는 빌드에서는 기본 텍스트 폰트 재사용
            self.fntAscii = self.fntText

        # ascii 전용 Bold 폰트
        self.fntAsciiBold = None

        # 1순위: res/freesansbold.ttf
        self.fntFreeSansBold = None
        try:
            resfolder = getattr(common.common, 'resfolder', None)
            if resfolder:
                fsb_path = os.path.join(resfolder, 'freesansbold.ttf')
                if os.path.exists(fsb_path):
                    self.fntFreeSansBold = ImageFont.truetype(fsb_path, int(self.FONT_SIZE))
        except Exception:
            self.fntFreeSansBold = None

        if self.fntFreeSansBold is not None:
            # 경도/도데카 Bold 는 무조건 FreeSansBold 사용
            self.fntAsciiBold = self.fntFreeSansBold
        else:
            # 2순위: abc_ascii_bold (빌드에 있을 때)
            try:
                ascii_bold_path = getattr(common.common, 'abc_ascii_bold', None)
                if ascii_bold_path:
                    self.fntAsciiBold = ImageFont.truetype(ascii_bold_path, int(self.FONT_SIZE))
            except Exception:
                self.fntAsciiBold = None

        # 그래도 없으면 그냥 일반 ascii 폰트 재사용
        if self.fntAsciiBold is None:
            self.fntAsciiBold = self.fntAscii

        # >>> Eclipses: 경도/도데카 Bold 숫자는 common.freesans_bold를 강제 사용 <<<
        try:
            self.fntAsciiBold = ImageFont.truetype(common.common.freesans_bold, int(self.FONT_SIZE))
        except Exception:
            # FreeSansBold 로드 실패 시 기존 설정 유지
            pass

        self.signs = common.common.Signs1 if self.options.signs else common.common.Signs2

        # 아야남샤(시데럴) 사용 여부: 옵션 키 존재/값 기반으로 유연 탐지
        self._ayan_enabled = bool(getattr(self.options, 'ayanamsha', 0) or
                                  getattr(self.options, 'ayanamsa', 0) or
                                  getattr(self.options, 'sidereal', False) or
                                  getattr(self.options, 'siderealmode', False))

        # 데이터 생성
        with wx.BusyCursor():
            try:
                self.rows = eclipses.find_eclipses_around(chrt)
            except Exception as e:
                wx.MessageBox(u"Eclipses failed:\n%s" % e, "Error", wx.OK|wx.ICON_ERROR, self)
                self.rows = []

        # 테이블 폭/높이 계산
        self.cols = (
            mtexts.txts['Date'],
            mtexts.txts['Type'],
            mtexts.txts['Longitude'],
            mtexts.txts['Dodecatemorion'],
        )
        self.colw = tuple([self.CELL_WIDTH] * len(self.cols))
        self.chart = chrt
        self.TABLE_WIDTH  = self.SMALL_CELL_WIDTH + sum(self.colw)
        self.LINE_NUM     = len(self.rows)      # 헤더는 TITLE_HEIGHT로 이미 반영
        self.TABLE_HEIGHT = self.TITLE_HEIGHT + self.SPACE_TITLEY + self.LINE_NUM*self.LINE_HEIGHT
        self.WIDTH  = int(commonwnd.CommonWnd.BORDER + self.TABLE_WIDTH + commonwnd.CommonWnd.BORDER)
        self.HEIGHT = int(commonwnd.CommonWnd.BORDER + self.TABLE_HEIGHT + commonwnd.CommonWnd.BORDER)
        self.SetVirtualSize((self.WIDTH, self.HEIGHT))

        self.drawBkg()

    def getExt(self):
        return u"eclipses.bmp"

    def _deg_min_sec_text(self, degfloat):
        d, m, s = eclipses._dms(degfloat)
        return u"%d%s%02d'%02d\"" % (d, self.deg_symbol, m, s)

    def _dodek_text(self, sign_idx, d, m, s):
        # 여기선 직접 포맷만 담당(계산은 eclipses._dodek_from_ecliptic에서 수행)
        dms = u"%d%s%02d'%02d\"" % (d, self.deg_symbol, m, s)
        return dms, self.signs[sign_idx]

    def _text(self, draw, xy, s, bold=False, font=None, fill=(0,0,0)):
        """
        공용 텍스트 출력 헬퍼.
        - Morinus 심볼(별자리, 행성 등): bold=True이면 두 번 찍는 가짜 볼드
        - 영어 숫자/각도(abc_ascii): bold=True이면 fntAsciiBold 사용
        - 일반 텍스트(다국어 UI): bold=True이면 fntTextBold 사용
        """
        if font is None:
            font = self.fntText

        # 1) 사인/행성 기호: Morinus 심볼 폰트 → 가짜 볼드(두 번 찍기)
        if bold and font is self.fntMorinus:
            x, y = xy
            draw.text((x+1, y), s, fill=fill, font=font)
            draw.text((x,   y), s, fill=fill, font=font)
            return

        # 2) 영어 숫자/각도용 폰트: abc_ascii 계열
        if hasattr(self, 'fntAscii') and font is self.fntAscii:
            if bold:
                # ① abc_ascii_bold → ② res/freesansbold.ttf → ③ 기본 ascii
                local_font = getattr(self, 'fntAsciiBold', None)
                if not local_font:
                    local_font = getattr(self, 'fntFreeSansBold', None) or self.fntAscii
                draw.text(xy, s, fill=fill, font=local_font)
                return
            else:
                draw.text(xy, s, fill=fill, font=font)
                return

        # 3) 나머지 일반 텍스트: 다국어 UI용 폰트 + Bold
        if bold:
            try:
                font = self.fntTextBold or font
            except AttributeError:
                font = font

        draw.text(xy, s, fill=fill, font=font)

    def _ayan_deg(self, jdut):
        """이벤트 시점(jdut)의 아야남샤(도) — 옵션 미사용이면 0.0"""
        if not getattr(self, '_ayan_enabled', False):
            return 0.0
        try:
            # Swiss Ephemeris 래퍼 (Morinus 기본 의존): 존재 시 사용
            return float(astrology.swe_get_ayanamsa_ut(jdut))
        except Exception:
            # 환경에 따라 심볼이 다를 수 있으니 실패 시 무효 처리(트로피컬 유지)
            return 0.0
            
    def _dodek_from_lon(self, Ldeg):
        """
        절대 경도 Ldeg(0..360) → (결과 사인, 그 사인 안의 도·분·초).
        규칙:
          base_sign   = floor(L/30)
          within      = L - base_sign*30           # 0.. <30
          total_arc   = within * 12.0              # 0.. <360
          sign_offset = floor(total_arc / 30.0)    # 0..11
          sign_idx    = (base_sign + sign_offset) % 12
          inner       = total_arc - sign_offset*30 # 0.. <30
        """
        L = eclipses._normalize_deg(float(Ldeg))
        base_sign = int(math.floor(L / 30.0)) % 12
        within = L - base_sign * 30.0

        total_arc = within * 12.0
        sign_offset = int(math.floor(total_arc / 30.0 + 1e-12))
        sign_idx = (base_sign + sign_offset) % 12

        inner = total_arc - sign_offset * 30.0  # 이 값이 사인 내부각(0.. <30)

        d = int(math.floor(inner + 1e-9))
        rem = (inner - d) * 60.0
        m = int(math.floor(rem + 1e-9))
        s = int(round((rem - m) * 60.0))

        # 자리올림 정규화
        if s >= 60:
            s -= 60; m += 1
        if m >= 60:
            m -= 60; d += 1
        if d >= 30:
            d -= 30
            sign_idx = (sign_idx + 1) % 12

        return sign_idx, d, m, s

    def drawBkg(self):
        opt = getattr(self, 'options', None)

        def _col(name, default):
            # 흑백 출력이면 default 강제
            if self.bw:
                return default
            # options 객체가 없거나 속성이 없으면 default
            if opt is None:
                return default
            return getattr(opt, name, default)

        self.bkgclr = _col('clrbkg', (255, 255, 255))
        tableclr    = _col('clrframe', (0, 0, 0))
        txtclr      = _col('clrtexts', (0, 0, 0))

        img = Image.new('RGB', (self.WIDTH, self.HEIGHT), self.bkgclr)
        draw = ImageDraw.Draw(img)
        BOR = commonwnd.CommonWnd.BORDER

        # 테두리 박스
        draw.rectangle(((BOR, BOR),(BOR+self.TABLE_WIDTH, BOR+self.TABLE_HEIGHT)), outline=tableclr, fill=self.bkgclr)

        # 헤더 바
        draw.rectangle(((BOR+self.SMALL_CELL_WIDTH, BOR),(BOR+self.TABLE_WIDTH, BOR+self.TITLE_HEIGHT)),
                    outline=None, fill=self.bkgclr)  # 헤더 내부 세로선 제거
        # 헤더 텍스트
        x = BOR + self.SMALL_CELL_WIDTH
        for i, head in enumerate(self.cols):
            w,h = draw.textsize(head, self.fntText)
            cy = BOR + (self.TITLE_HEIGHT - h)//2
            draw.text((x + (self.colw[i]-w)//2, cy), head, fill=txtclr, font=self.fntText)
            x += self.colw[i]

        # 헤더 하단 라인
        y = BOR + self.TITLE_HEIGHT
        draw.line((BOR, y, BOR+self.TABLE_WIDTH, y), fill=tableclr)

        # (복원) 상단 가로선 + 우측 세로 테두리
        draw.line((BOR, BOR, BOR+self.TABLE_WIDTH, BOR), fill=tableclr)
        draw.line((BOR+self.TABLE_WIDTH, BOR, BOR+self.TABLE_WIDTH, BOR+self.TABLE_HEIGHT), fill=tableclr)

        # (NEW) 세로선: 번호칸 제외, 헤더 아래부터 표 하단까지
        x = BOR + self.SMALL_CELL_WIDTH
        xpos = [x]
        for w in self.colw[:-1]:
            x += w
            xpos.append(x)
        y0 = y + self.SPACE_TITLEY
        y1 = BOR + self.TABLE_HEIGHT
        for xv in xpos:
            draw.line((xv, y0, xv, y1), fill=tableclr)

        # 데이터 행
        y += self.SPACE_TITLEY
        rowy = y
        for idx, ev in enumerate(self.rows, start=1):
            # 왼쪽 번호칸
            num = u"%d" % idx
            w,h = draw.textsize(num, self.fntText)
            draw.text((BOR + (self.SMALL_CELL_WIDTH - w)//2, rowy + (self.LINE_HEIGHT - h)//2),
                      num, fill=txtclr, font=self.fntText)

            # 각 열 내용
            colx = BOR + self.SMALL_CELL_WIDTH

            # 1) Date (LOCAL, 날짜만 '.' 구분)
            dt = eclipses.local_date_string(ev.jdut, self.chart)
            w,h = draw.textsize(dt, self.fntText)
            draw_xy = (colx + (self.colw[0]-w)//2, rowy + (self.LINE_HEIGHT-h)//2)
            self._text(draw, draw_xy, dt, bold=ev.bold, font=self.fntText, fill=txtclr)
            colx += self.colw[0]

            # 2) Type
            # 분류 토큰 → 다국어 문자열 매핑
            _kind_text = {
                u"TOTAL":     mtexts.txts['Total2'],
                u"ANNULAR":   mtexts.txts['Annular'],
                u"HYBRID":    mtexts.txts['Hybrid'],
                u"PARTIAL":   mtexts.txts['Partial'],
                u"PENUMBRAL": mtexts.txts['Penumbral'],
                u"UNKNOWN":   mtexts.txts['Unknown'],
            }

            if ev.is_solar:
                kind, _, _ = eclipses._classify_solar_from_retflag(int(ev.retflag) if not isinstance(ev.retflag,(list,tuple)) else int(ev.retflag[0]))
                type_txt = u"%s: %s" % (mtexts.txts['Solar2'], _kind_text.get(kind, mtexts.txts['Unknown']))
            else:
                kind, _, _ = eclipses._classify_lunar_from_retflag(int(ev.retflag) if not isinstance(ev.retflag,(list,tuple)) else int(ev.retflag[0]))
                type_txt = u"%s: %s" % (mtexts.txts['Lunar2'], _kind_text.get(kind, mtexts.txts['Unknown']))
            w,h = draw.textsize(type_txt, self.fntText)
            draw_xy = (colx + (self.colw[1]-w)//2, rowy + (self.LINE_HEIGHT-h)//2)
            self._text(draw, draw_xy, type_txt, bold=ev.bold, font=self.fntText, fill=txtclr)
            colx += self.colw[1]

            # 3) Longitude: 사인 + 도분초 (아야남샤 적용)
            ayan = self._ayan_deg(ev.jdut)
            Lsid = eclipses._normalize_deg(ev.elon - ayan) if ayan else eclipses._normalize_deg(ev.elon)
            sign_idx = int(math.floor((Lsid + 1e-12)/30.0)) % 12
            within = Lsid - sign_idx*30.0
            d, m, s = eclipses._dms(within)

            # 숫자 + 사인기호
            lon_dms = u"%d%s%02d'%02d\"" % (d, self.deg_symbol, m, s)

            # 숫자는 영어폰트(abc_ascii), 사인기호는 Morinus 심볼
            num_font       = getattr(self, 'fntAscii', self.fntText)
            bold_num_font  = getattr(self, 'fntAsciiBold', num_font)

            # 실제 그릴 폰트(볼드 여부에 따라 선택)
            draw_num_font = bold_num_font if ev.bold else num_font

            w_num, h_num = draw.textsize(lon_dms+u" ", draw_num_font)
            w_sig, h_sig = draw.textsize(self.signs[sign_idx], self.fntMorinus)
            total_w = w_num + w_sig
            base_x = colx + (self.colw[2]-total_w)//2

            # 숫자 (경도 DMS) – 여기서만 직접 FreeSansBold/AsciiBold 사용
            draw.text(
                (base_x, rowy + (self.LINE_HEIGHT-h_num)//2),
                lon_dms+u" ",
                fill=txtclr,
                font=draw_num_font
            )

            # 사인기호(볼드면 두 번 찍기 규칙 적용, Morinus 심볼 폰트 유지)
            self._text(draw,
                       (base_x + w_num, rowy + (self.LINE_HEIGHT-h_sig)//2),
                       self.signs[sign_idx],
                       bold=ev.bold,
                       font=self.fntMorinus,
                       fill=txtclr)

            colx += self.colw[2]

            # 4) Dodecatemorion — 숫자+DMS와 사인기호 묶어서 가운데 정렬 (아야남샤 적용)
            ayan = self._ayan_deg(ev.jdut)
            Lsid = eclipses._normalize_deg(ev.elon - ayan) if ayan else eclipses._normalize_deg(ev.elon)

            # eclipses 모듈의 도데카 변환에 시데럴 경도 전달
            try:
                dodek_sign, dd, mm, ss = eclipses._dodek_from_ecliptic(Lsid)
            except Exception:
                # (FIX) 아야남샤 적용된 경도 Lsid로 직접 도데카 산출
                dodek_sign, dd, mm, ss = self._dodek_from_lon(Lsid)

            dms_txt, sign_sym = self._dodek_text(dodek_sign, dd, mm, ss)

            # 도데카 숫자도 영어폰트(abc_ascii) 사용
            num_font       = getattr(self, 'fntAscii', self.fntText)
            bold_num_font  = getattr(self, 'fntAsciiBold', num_font)
            draw_num_font  = bold_num_font if ev.bold else num_font

            w_num, h_num = draw.textsize(dms_txt+u" ", draw_num_font)
            w_sig, h_sig = draw.textsize(sign_sym, self.fntMorinus)
            total_w = w_num + w_sig
            base_x = colx + (self.colw[3]-total_w)//2

            # 숫자 (도데카 DMS)
            draw.text(
                (base_x, rowy + (self.LINE_HEIGHT-h_num)//2),
                dms_txt+u" ",
                fill=txtclr,
                font=draw_num_font
            )

            # 사인 기호
            self._text(draw,
                       (base_x + w_num, rowy + (self.LINE_HEIGHT-h_sig)//2),
                       sign_sym,
                       bold=ev.bold,
                       font=self.fntMorinus,
                       fill=txtclr)

            colx += self.colw[3]

            # 행 구분 라인
            draw.line((BOR, rowy + self.LINE_HEIGHT, BOR+self.TABLE_WIDTH, rowy + self.LINE_HEIGHT), fill=tableclr)
            rowy += self.LINE_HEIGHT

        # wx 비트맵 갱신
        wxImg = wx.Image(img.size[0], img.size[1])
        wxImg.SetData(img.tobytes())
        self.buffer = wx.Bitmap(wxImg)
