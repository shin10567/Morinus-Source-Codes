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
        self.fntText    = ImageFont.truetype(common.common.abc, int(self.FONT_SIZE))
        self.fntTextBold = None  # 볼드 미사용 고정

        self.signs = common.common.Signs1 if self.options.signs else common.common.Signs2

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
        return u"%02d%s%02d'%02d\"" % (d, self.deg_symbol, m, s)

    def _dodek_text(self, sign_idx, d, m, s):
        # 여기선 직접 포맷만 담당(계산은 eclipses._dodek_from_ecliptic에서 수행)
        dms = u"%02d%s%02d'%02d\"" % (d, self.deg_symbol, m, s)
        return dms, self.signs[sign_idx]

    def _text(self, draw, xy, s, bold=False, font=None, fill=(0,0,0)):
        # 볼드 완전 비활성: 항상 한 번만 그린다
        if font is None:
            font = self.fntText
        draw.text(xy, s, fill=fill, font=font)

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

            # 3) Longitude: 사인 + 도분초
            # 사인/도분초 분해
            L = eclipses._normalize_deg(ev.elon)
            sign_idx = int(math.floor((L + 1e-12)/30.0)) % 12
            within = L - sign_idx*30.0
            d, m, s = eclipses._dms(within)
            # 숫자 + 사인기호
            lon_dms = u"%02d%s%02d'%02d\"" % (d, self.deg_symbol, m, s)
            w_num, h_num = draw.textsize(lon_dms+u" ", self.fntText)
            w_sig, h_sig = draw.textsize(self.signs[sign_idx], self.fntMorinus)
            total_w = w_num + w_sig
            base_x = colx + (self.colw[2]-total_w)//2
            # 숫자
            self._text(draw, (base_x, rowy + (self.LINE_HEIGHT-h_num)//2), lon_dms+u" ",
                    bold=ev.bold, font=self.fntText, fill=txtclr)

            # 사인기호(볼드면 두 번 찍기 규칙 적용)
            self._text(draw, (base_x + w_num, rowy + (self.LINE_HEIGHT-h_sig)//2),
                    self.signs[sign_idx], bold=ev.bold, font=self.fntMorinus, fill=txtclr)

            colx += self.colw[2]

            # 4) Dodecatemorion — 숫자+DMS와 사인기호 묶어서 가운데 정렬
            dms_txt, sign_sym = self._dodek_text(ev.dodek_sign, ev.dodek_d, ev.dodek_m, ev.dodek_s)
            w_num, h_num = draw.textsize(dms_txt+u" ", self.fntText)
            w_sig, h_sig = draw.textsize(sign_sym, self.fntMorinus)
            total_w = w_num + w_sig
            base_x = colx + (self.colw[3]-total_w)//2
            self._text(draw, (base_x, rowy + (self.LINE_HEIGHT-h_num)//2),
                    dms_txt+u" ", bold=ev.bold, font=self.fntText, fill=txtclr)
            self._text(draw, (base_x + w_num, rowy + (self.LINE_HEIGHT-h_sig)//2),
                    sign_sym, bold=ev.bold, font=self.fntMorinus, fill=txtclr)
            colx += self.colw[3]

            # 행 구분 라인
            draw.line((BOR, rowy + self.LINE_HEIGHT, BOR+self.TABLE_WIDTH, rowy + self.LINE_HEIGHT), fill=tableclr)
            rowy += self.LINE_HEIGHT

        # wx 비트맵 갱신
        wxImg = wx.Image(img.size[0], img.size[1])
        wxImg.SetData(img.tobytes())
        self.buffer = wx.Bitmap(wxImg)
