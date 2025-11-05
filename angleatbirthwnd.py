# -*- coding: utf-8 -*-
import wx
import os
import common
import re  # ← 추가
import commonwnd
import Image, ImageDraw, ImageFont   # ← fixstars와 동일한 PIL 사용
from angleatbirth import compute_contacts
import mtexts

class AngleAtBirthWnd(commonwnd.CommonWnd):

    def _to_hhmmss(self, s):
        """
        임의의 time_str에서 시·분·초를 뽑아 항상 'hh:mm:ss'로 돌려준다.
        - '12:34', '12:34:56', '12.34', '12.34.56', '12h34m56s' 등 처리
        - 문자열 어딘가에 날짜가 있어도 마지막 시간 구간만 잡는다.
        - 못 찾으면 원문 반환(최소 안전장치)
        """
        if not s:
            return u"-"
        s = s.strip()

        # 1) 'HH:MM[:SS]' 또는 'HH.MM[.SS]' → 마지막 매치를 선택
        m_all = re.findall(r'(\d{1,2})[:.](\d{1,2})(?:[:.](\d{1,2}))?', s)
        if m_all:
            h, mi, se = m_all[-1]
            return u"%02d:%02d:%02d" % (int(h), int(mi), int(se or 0))

        # 2) '12h34m56s' 같은 형태
        m = re.search(r'(\d{1,2})h(\d{1,2})m(?:(\d{1,2})s)?', s, re.I)
        if m:
            h = int(m.group(1)); mi = int(m.group(2)); se = int(m.group(3) or 0)
            return u"%02d:%02d:%02d" % (h, mi, se)

        # 3) 최후의 수단: 전체를 점→콜론 치환
        if '.' in s and ':' not in s:
            return s.replace('.', ':')
        return s

    def __init__(self, parent, chrt, options, mainfr, minutes=None, id=-1, size=wx.DefaultSize):
        commonwnd.CommonWnd.__init__(self, parent, chrt, options, id, size)
        self.mainfr  = mainfr
        self.chart   = chrt
        self.options = options
        self.minutes = int(minutes or 10)

        # === fixstarswnd 규격 준용 ===
        self.FONT_SIZE = int(21*self.options.tablesize)          # 글자 크기
        self.SPACE     = self.FONT_SIZE/2                        # 위/아래 여백
        self.LINE_HEIGHT = (self.SPACE + self.FONT_SIZE + self.SPACE)
        self.fntText   = ImageFont.truetype(common.common.abc, self.FONT_SIZE)
        self.fntBold   = ImageFont.truetype(common.common.abc_bold, self.FONT_SIZE)

        # 컬럼: Δt, Star, Angle, Exact Time  (폭은 픽스드스타 방식처럼 글꼴 크기 기반)
        self.W_DT   = 5 * self.FONT_SIZE
        self.W_STAR = 10 * self.FONT_SIZE
        self.W_ANG  = 5  * self.FONT_SIZE
        self.W_TIME = 8  * self.FONT_SIZE
        self.COLUMN_NUM  = 4
        self.TITLE_HEIGHT = self.LINE_HEIGHT
        self.TITLE_WIDTH  = (self.W_DT + self.W_STAR + self.W_ANG + self.W_TIME)
        self.TABLE_WIDTH  = self.TITLE_WIDTH

        self.rows = []
        self._compute()

        self.drawBkg()
        self.Bind(wx.EVT_SIZE, self._onResize)

    def getExt(self):
        # 공통 저장 메뉴에서 파일명에 덧붙일 접미사. (fixstars는 mtexts['Fix'] 사용)
        return u"AngleAtBirth.bmp"

    def _onResize(self, evt):
        # 고정 레이아웃이지만 리사이즈 시 다시 그려 일관 유지
        self.drawBkg()
        evt.Skip()

    def _compute(self):
        try:
            self.rows = compute_contacts(self.chart, self.options, self.minutes) or []
            # ⬇️ time_str을 항상 'hh:mm:ss'로 통일
            for r in self.rows:
                r['time_str'] = self._to_hhmmss(r.get('time_str', u""))
        except Exception as e:
            self.rows = []
            wx.MessageBox(u"Angle at Birth error\n\n%s" % (e,), u"Angle at Birth")
    
    def _should_bold(self, mag, dt_min):
        """겉보기등급(mag)과 Δt(분)으로 이 행을 Bold 처리할지 결정."""
        try:
            if mag is None:
                return False
            dm = float(dt_min or 0.0)

            if mag < 0.0:
                return dm <= 8.0
            if 0.0 <= mag < 1.0:
                return dm <= 6.0
            if 1.0 <= mag < 1.5:
                return dm <= 5.0
            if mag >= 1.5:
                return dm <= 4.0
            return False
        except Exception:
            return False

    def drawBkg(self):
        # === 색상/배경 ===
        if self.bw:
            self.bkgclr = (255,255,255)
        else:
            self.bkgclr = self.options.clrbackground
        self.SetBackgroundColour(self.bkgclr)

        tableclr = self.options.clrtable if not self.bw else (0,0,0)
        txtclr   = (0,0,0) if self.bw else self.options.clrtexts

        BOR = commonwnd.CommonWnd.BORDER
        rows_n = len(self.rows)

        table_height = self.TITLE_HEIGHT if rows_n == 0 else (self.TITLE_HEIGHT + rows_n * self.LINE_HEIGHT)
        width  = BOR + self.TITLE_WIDTH  + BOR
        height = BOR + table_height      + BOR

        # 버퍼/스크롤
        self.SetVirtualSize((int(width), int(height)))
        img  = Image.new('RGB', (int(width), int(height)), self.bkgclr)
        draw = ImageDraw.Draw(img)

        # 헤더 배경 (fixstars 톤)
        draw.rectangle(((BOR, BOR), (BOR + self.TITLE_WIDTH, BOR + self.TITLE_HEIGHT)),
                    outline=tableclr, fill=self.bkgclr)

        # 헤더 텍스트 중앙정렬
        heads = (u"\u0394T", mtexts.txts["FixedStar"], mtexts.txts["Angle"], mtexts.txts["ExactTime"])
        col_w = (self.W_DT, self.W_STAR, self.W_ANG, self.W_TIME)
        x = BOR
        for i, h in enumerate(heads):
            tw, th = draw.textsize(h, self.fntText)
            draw.text((x + (col_w[i]-tw)/2, BOR + (self.TITLE_HEIGHT-th)/2),
                    h, fill=txtclr, font=self.fntText)
            x += col_w[i]

        # 헤더 하단선
        x0 = BOR
        y0 = BOR + self.TITLE_HEIGHT
        draw.line((x0, y0, x0 + self.TITLE_WIDTH, y0), fill=tableclr)

        # 세로 구분선: 표 전체 높이 기준으로 1회만
        xv = x0
        draw.line((xv, y0, xv, BOR + table_height), fill=tableclr)  # 왼쪽(헤더 제외)

        for w in col_w[:-1]:  # 내부 경계만 (마지막은 외곽선으로 대체)
            xv += w
            draw.line((xv, y0, xv, BOR + table_height), fill=tableclr)
        # 데이터
        if rows_n > 0:
            for i in range(rows_n):
                self._drawline(draw, x0, y0 + i*self.LINE_HEIGHT, tableclr, txtclr, i)
        # 외곽 테두리
        draw.rectangle(((BOR, BOR), (BOR + self.TITLE_WIDTH, BOR + table_height)), outline=tableclr)

        # wx로 전송
        wxImg = wx.Image(img.size[0], img.size[1])
        wxImg.SetData(img.tobytes())
        self.buffer = wx.Bitmap(wxImg)
        self.Refresh()

    def _drawline(self, draw, x, y, clr, txtclr, idx):
        # 행 하단 가로선
        draw.line((x, y + self.LINE_HEIGHT, x + self.TITLE_WIDTH, y + self.LINE_HEIGHT), fill=clr)

        # 중앙정렬 셀 텍스트
        r = self.rows[idx]
        is_bold = self._should_bold(r.get('mag'), r.get('dt_min'))
        cells = (
            u"\u00B1%.1f'" % float(r.get('dt_min', 0.0)),  # Δt: ± 기호 고정
            r.get('star',  u"-"),
            r.get('angle', u"-"),
            r.get('time_str', u"-"),
        )
        col_w = (self.W_DT, self.W_STAR, self.W_ANG, self.W_TIME)
        xx = x
        for i in range(4):
            font = self.fntBold if is_bold else self.fntText
            tw, th = draw.textsize(cells[i], font)
            draw.text((xx + (col_w[i]-tw)/2, y + (self.LINE_HEIGHT - th)/2),
                      cells[i], fill=txtclr, font=font)
            xx += col_w[i]

