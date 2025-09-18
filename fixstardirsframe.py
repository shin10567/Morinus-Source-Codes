# -*- coding: utf-8 -*-
import wx, os, math, datetime
from PIL import Image, ImageDraw, ImageFont
import common, commonwnd as cw, mtexts, astrology, util
import fixstardirs
import primdirs

# ---------- 테이블(프라이머리 디렉션 스타일, CommonWnd 상속) ----------
class FixStarDirsWnd(cw.CommonWnd):
    SCROLL_RATE = 20
    BORDER = 20

    def __init__(self, parent, chrt, options, mainfr=None, id=-1, size=wx.DefaultSize):
        cw.CommonWnd.__init__(self, parent, chrt, options, id, size)
        self.parent  = parent
        self.chart   = chrt
        self.options = options
        self.mainfr  = mainfr
        self.bw      = self.options.bw

        # 프라이머리 디렉션과 같은 스케일
        self.FONT_SIZE   = int(21 * self.options.tablesize)
        self.SPACE       = (self.FONT_SIZE / 2)
        self.LINE_HEIGHT = (self.SPACE + self.FONT_SIZE + self.SPACE)
        self.LINE_NUM    = 40             # 한 컬럼 표시에 보일 행 수 (세로로 길게 → 넘치면 오른쪽 컬럼)

        # 폭: Prom 넓게, Arc 약간 좁게
        self.SMALL_CELL_WIDTH = (4 * self.FONT_SIZE)
        self.CELL_WIDTH       = (6 * self.FONT_SIZE)
        self.BIG_CELL_WIDTH   = (10 * self.FONT_SIZE)
        self.MED_CELL_WIDTH   = (7 * self.FONT_SIZE)
        self.W_AGE  = self.SMALL_CELL_WIDTH
        self.W_PROM = self.BIG_CELL_WIDTH
        self.W_DC   = self.SMALL_CELL_WIDTH
        self.W_SIG  = self.CELL_WIDTH
        self.W_ARC  = self.CELL_WIDTH  
        self.W_DATE = self.MED_CELL_WIDTH
        self.COL_WIDTHS = (self.W_AGE, self.W_PROM, self.W_DC, self.W_SIG, self.W_ARC, self.W_DATE)
        self.COLUMN_NUM = 6

        self.SPACE_TITLEY         = 4
        self.TITLE_CELL_HEIGHT    = (2 * self.LINE_HEIGHT)
        self.TABLE_WIDTH          = sum(self.COL_WIDTHS)
        self.SPACE_BETWEEN_TABLESX= 4
        self.TITLE_CELL_WIDTH     = (2 * self.TABLE_WIDTH + self.SPACE_BETWEEN_TABLESX + 1)
        self.SECOND_TABLE_OFFSX   = (self.TABLE_WIDTH + self.SPACE_BETWEEN_TABLESX)

        self.WIDTH  = (FixStarDirsWnd.BORDER + self.TITLE_CELL_WIDTH + FixStarDirsWnd.BORDER)
        self.TABLE_HEIGHT = (self.TITLE_CELL_HEIGHT + self.SPACE_TITLEY + self.LINE_NUM * self.LINE_HEIGHT)
        self.HEIGHT = (FixStarDirsWnd.BORDER + self.TABLE_HEIGHT + FixStarDirsWnd.BORDER)
        self.SetVirtualSize((self.WIDTH, self.HEIGHT))

        # 폰트
        self.fntMorinus = ImageFont.truetype(common.common.symbols, self.FONT_SIZE)
        self.fntSymbol  = ImageFont.truetype(common.common.symbols, 3 * self.FONT_SIZE / 2)   # D/C 화살표용 '-'
        self.fntAspects = ImageFont.truetype(common.common.symbols, 3 * self.FONT_SIZE / 4)   # 각 기호
        self.fntText    = ImageFont.truetype(common.common.abc,     self.FONT_SIZE)

        # 색상
        self.bkgclr   = (255, 255, 255) if self.bw else self.options.clrbackground
        self.tableclr = (0, 0, 0)       if self.bw else self.options.clrtable
        self.txtclr   = (0, 0, 0)       if self.bw else self.options.clrtexts
        self.SetBackgroundColour(self.bkgclr)

        # 데이터 / 페이지 상태
        self.rows     = []
        self.currpage = 1
        self.maxpage  = 1
        self.fr       = 0
        self.to       = 0

        self._ensure_save_dir()
        self.drawBkg()

    # 공통 저장 기능용
    def getExt(self):
        return u"fixedstarsdir.bmp"

    def _ensure_save_dir(self):
        try:
            imgdir = getattr(self.options, 'fpathimgs', None)
            if not imgdir:
                try:
                    base = util.getDocDir()
                except Exception:
                    base = os.getcwd()
                imgdir = os.path.join(base, u"images")
            if not os.path.isdir(imgdir):
                os.makedirs(imgdir)
            if self.mainfr is not None and not hasattr(self.mainfr, 'fpathimgs'):
                self.mainfr.fpathimgs = imgdir
        except Exception:
            pass

    # 외부에서 데이터/페이지 지정
    def set_data(self, rows, currpage, maxpage, fr, to):
        self.rows     = rows or []
        self.currpage = currpage
        self.maxpage  = maxpage
        self.fr       = fr
        self.to       = to
        # 가로 1컬럼/2컬럼 동적 폭
        total = self.to - self.fr
        if total <= self.LINE_NUM:
            self.TITLE_CELL_WIDTH = self.TABLE_WIDTH
            self.WIDTH = FixStarDirsWnd.BORDER + self.TITLE_CELL_WIDTH + FixStarDirsWnd.BORDER
        else:
            self.TITLE_CELL_WIDTH = 2 * self.TABLE_WIDTH + self.SPACE_BETWEEN_TABLESX + 1
            self.WIDTH = FixStarDirsWnd.BORDER + self.TITLE_CELL_WIDTH + FixStarDirsWnd.BORDER
        self.SetVirtualSize((self.WIDTH, self.HEIGHT))
        self.drawBkg()

    def display(self, currpage, fr, to, maxpage):
        self.currpage = currpage
        self.fr, self.to = fr, to
        self.maxpage = maxpage
        self.drawBkg()
        try:
            self.Refresh(False); self.Update()
        except:
            pass

    # 포맷 유틸
    def _fmt_date(self, jd=None, d=None):
        # yyyy.mm.dd (시/분 제거)
        if isinstance(d, datetime.date):
            return u"%04d.%02d.%02d" % (d.year, d.month, d.day)
        if jd:
            y, m, dd, _ = astrology.swe_revjul(jd, astrology.SE_GREG_CAL)
            return u"%04d.%02d.%02d" % (y, m, dd)
        try:
            s = unicode(d).split(u' ')[0].replace(u'-', u'.')
            y, m, dd = map(int, s.split(u'.')[:3])
            return u"%04d.%02d.%02d" % (y, m, dd)
        except Exception:
            return u""

    def _age_years(self, birth_jd, event_jd=None, event_date=None):
        if event_jd and birth_jd:
            return (event_jd - birth_jd) / 365.2425
        if isinstance(event_date, datetime.date) and birth_jd:
            by, bm, bd, _ = astrology.swe_revjul(birth_jd, astrology.SE_GREG_CAL)
            return (event_date.toordinal() - datetime.date(by, bm, bd).toordinal()) / 365.2425
        return None
    def _pd_key_title(self):
        opt = self.options
        # 동적 키
        if getattr(opt, 'pdkeydyn', False):
            d = getattr(opt, 'pdkeyd', None)
            if d == primdirs.PrimDirs.TRUESOLAREQUATORIALARC:
                return u"Dynamic Key: True Solar (Equatorial)"
            if d == primdirs.PrimDirs.TRUESOLARECLIPTICALARC:
                return u"Dynamic Key: True Solar (Ecliptical)"
            if d == primdirs.PrimDirs.BIRTHDAYSOLAREQUATORIALARC:
                return u"Dynamic Key: Birthday Solar (Equatorial)"
            if d == primdirs.PrimDirs.BIRTHDAYSOLARECLIPTICALARC:
                return u"Dynamic Key: Birthday Solar (Ecliptical)"
            return u"Dynamic Key"
        # 정적 키
        s = getattr(opt, 'pdkeys', None)
        if s == primdirs.PrimDirs.NAIBOD:
            return u"Static Key: Naibod"
        if s == primdirs.PrimDirs.CARDAN:
            return u"Static Key: Cardan"
        if s == primdirs.PrimDirs.PTOLEMY:
            return u"Static Key: Ptolemy"
        if s == primdirs.PrimDirs.CUSTOMER:
            # 사용자 지정 값 표시(도/분/초)
            deg = getattr(opt, 'pdkeydeg', 0)
            minu = getattr(opt, 'pdkeymin', 0)
            sec = getattr(opt, 'pdkeysec', 0)
            return u"Static Key: Custom (%d° %d′ %d″)" % (deg, minu, sec)
        # 안전망(기본)
        return u"Static Key: Naibod"

    # 그리기
    def drawBkg(self):
        img  = Image.new('RGB', (max(self.WIDTH,1), max(self.HEIGHT,1)), self.bkgclr)
        draw = ImageDraw.Draw(img)

        BOR = FixStarDirsWnd.BORDER

        # Title 박스
        draw.rectangle(((BOR, BOR), (BOR + self.TITLE_CELL_WIDTH, BOR + self.TITLE_CELL_HEIGHT)),
                       outline=self.tableclr, fill=self.bkgclr)
        keytxt = self._pd_key_title()
        title  = u"Mundane Only, " + keytxt
        tw, th = draw.textsize(title, self.fntText)
        draw.text((BOR + (self.TITLE_CELL_WIDTH - tw) / 2,
                   BOR + (self.LINE_HEIGHT - th) / 2),
                  title, fill=self.txtclr, font=self.fntText)

        # 우측 상단 페이지 표시 (파이썬2: % 포맷)
        ptxt = u"%d / %d" % (self.currpage, self.maxpage)
        pw, ph = draw.textsize(ptxt, self.fntText)
        draw.text((BOR + self.TITLE_CELL_WIDTH - pw - self.TITLE_CELL_WIDTH / 10,
                   BOR + (self.LINE_HEIGHT - ph) / 2),
                  ptxt, fill=self.txtclr, font=self.fntText)

        # 헤더 (좌/우 동일)
        headers = (u"Age", u"Prom.", u"D/C", u"Sig.", u"Arc", u"Date")
        # 왼쪽 헤더
        x = BOR; yhead = BOR + self.LINE_HEIGHT
        for i, w in enumerate(self.COL_WIDTHS):
            hw, hh = draw.textsize(headers[i], self.fntText)
            draw.text((x + (w - hw) / 2, yhead + (self.LINE_HEIGHT - hh) / 2),
                      headers[i], fill=self.txtclr, font=self.fntText)
            x += w
        # 오른쪽 헤더
        x = BOR + self.SECOND_TABLE_OFFSX
        for i, w in enumerate(self.COL_WIDTHS):
            hw, hh = draw.textsize(headers[i], self.fntText)
            draw.text((x + (w - hw) / 2, yhead + (self.LINE_HEIGHT - hh) / 2),
                      headers[i], fill=self.txtclr, font=self.fntText)
            x += w

        # 표 상단선 + 행들
        subset_len = max(0, self.to - self.fr)
        left_rows  = min(subset_len, self.LINE_NUM)
        right_rows = max(0, subset_len - left_rows)

        # 왼쪽 표
        x0 = BOR; y0 = BOR + self.TITLE_CELL_HEIGHT + self.SPACE_TITLEY
        draw.line((x0, y0, x0 + self.TABLE_WIDTH, y0), fill=self.tableclr)
        for i in range(left_rows):
            self._draw_row(draw, x0, y0 + i * self.LINE_HEIGHT, self.fr + i)

        # 오른쪽 표
        if right_rows > 0:
            x1 = BOR + self.SECOND_TABLE_OFFSX; y1 = BOR + self.TITLE_CELL_HEIGHT + self.SPACE_TITLEY
            draw.line((x1, y1, x1 + self.TABLE_WIDTH, y1), fill=self.tableclr)
            for i in range(right_rows):
                self._draw_row(draw, x1, y1 + i * self.LINE_HEIGHT, self.fr + left_rows + i)

        # 버퍼로 변환
        wximg = wx.EmptyImage(img.size[0], img.size[1])
        wximg.SetData(img.tobytes())
        self.buffer = wx.BitmapFromImage(wximg)

    def _draw_row(self, draw, x, y, ridx):
        # 하단 가로선
        draw.line((x, y + self.LINE_HEIGHT, x + self.TABLE_WIDTH, y + self.LINE_HEIGHT), fill=self.tableclr)
        # 세로선 + 외곽
        sumx = 0
        for w in self.COL_WIDTHS:
            draw.line((x + sumx, y, x + sumx, y + self.LINE_HEIGHT), fill=self.tableclr)
            sumx += w
        draw.line((x + self.TABLE_WIDTH, y, x + self.TABLE_WIDTH, y + self.LINE_HEIGHT), fill=self.tableclr)

        r = self.rows[ridx]
        tclr = self.txtclr

        # 1) Age (소수 2자리)
        birth_jd = getattr(self.chart.time, 'jd', None)
        evt_jd   = r.get('jd')
        evt_date = r.get('date') if isinstance(r.get('date'), datetime.date) else None
        age = self._age_years(birth_jd, event_jd=evt_jd, event_date=evt_date)
        agetxt = u"" if age is None else u"%.2f" % (age,)
        self._center_text(draw, x, y, 0, agetxt, self.fntText, tclr)

        # 2) Prom. (고정별 이름/표기 그대로)
        prom = unicode(r.get('prom', u""))
        self._center_text(draw, x, y, 1, prom, self.fntText, tclr)

        # 3) D/C (+ 화살표: 심볼 폰트 '-')
        d_is_direct = unicode(r.get('dc', u"D")).upper().startswith(u"D")
        dctxt = mtexts.txts['D'] if d_is_direct else mtexts.txts['C']
        cw = self.COL_WIDTHS[2]
        w_d, h_d = draw.textsize(dctxt, self.fntText)
        w_sp, _  = draw.textsize(u' ', self.fntText)
        w_arr, h_arr = draw.textsize(u'-', self.fntSymbol)
        off = (cw - (w_d + w_sp + w_arr)) / 2
        ox = x + sum(self.COL_WIDTHS[:2]) + off
        oy = y + (self.LINE_HEIGHT - h_d) / 2
        draw.text((ox, oy), dctxt, fill=tclr, font=self.fntText)
        draw.text((ox + w_d + w_sp, y + (self.LINE_HEIGHT - h_arr) / 2), u'-', fill=tclr, font=self.fntSymbol)

        # 4) Sig. (ASC/DSC → Asc/Dsc)
        sig_txt = unicode(r.get('sig', u"")).replace(u'ASC', u'Asc').replace(u'DSC', u'Dsc')
        self._center_text(draw, x, y, 3, sig_txt, self.fntText, tclr)

        # 5) Arc (소수 3자리 반올림)
        try:
            arc = float(r.get('arc', 0.0))
        except Exception:
            arc = 0.0
        arctxt = u"%.3f" % (arc,)
        self._center_text(draw, x, y, 4, arctxt, self.fntText, tclr)

        # 6) Date (yyyy.mm.dd)
        datetxt = self._fmt_date(jd=r.get('jd'), d=r.get('date'))
        self._center_text(draw, x, y, 5, datetxt, self.fntText, tclr)

    def _center_text(self, draw, x, y, colidx, txt, font, clr):
        start = x + sum(self.COL_WIDTHS[:colidx])
        wcol  = self.COL_WIDTHS[colidx]
        tw, th = draw.textsize(txt, font)
        draw.text((start + (wcol - tw) / 2, y + (self.LINE_HEIGHT - th) / 2), txt, fill=clr, font=font)

# ---------- 프레임(페이지 네비게이션 포함) ----------
class FixedStarDirsFrame(wx.Frame):
    def __init__(self, parent, title, horoscope, options):
        wx.Frame.__init__(self, parent, title=mtexts.txts.get('FixStarDirs', u"Angular Directions of Fixed Stars"))
        self.parent    = parent
        self.horoscope = horoscope
        self.options   = options

        # 전체 데이터 먼저 계산
        self.rows = fixstardirs.compute_fixedstar_angle_rows(self.horoscope, self.options, age_max_years=150.0)

        # 페이지 상태 (프라이머리와 동일 구조: 한 페이지 = 좌우 2컬럼)
        self.LINE_NUM  = 40
        self.page_cap  = self.LINE_NUM * 2
        self.currpage  = 1
        self.maxpage   = max(1, int(math.ceil(len(self.rows) / float(self.page_cap))))

        def _bounds(p):
            fr = (p - 1) * self.page_cap
            to = min(fr + self.page_cap, len(self.rows))
            return fr, to

        self.fr, self.to = _bounds(self.currpage)

        pnl  = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # 상단 네비(◀ ▶ + "현재/전체")
        hb = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_prev = wx.Button(pnl, wx.ID_ANY, u'◀', style=wx.BU_EXACTFIT)
        self.btn_next = wx.Button(pnl, wx.ID_ANY, u'▶', style=wx.BU_EXACTFIT)
        self.lbl_page = wx.StaticText(pnl, wx.ID_ANY, u"%d / %d" % (self.currpage, self.maxpage))
        self.btn_prev.Bind(wx.EVT_BUTTON, self.onPrevPage)
        self.btn_next.Bind(wx.EVT_BUTTON, self.onNextPage)

        hb.Add(self.btn_prev, 0, wx.RIGHT, 6)
        hb.Add(self.btn_next, 0, wx.RIGHT, 12)
        hb.Add(self.lbl_page, 0, wx.ALIGN_CENTER_VERTICAL)
        hb.AddStretchSpacer(1)
        
        # 테이블
        self.table = FixStarDirsWnd(pnl, self.horoscope, self.options, mainfr=self)
        self.table.set_data(self.rows, self.currpage, self.maxpage, self.fr, self.to)

        vbox.Add(hb, 0, wx.EXPAND | wx.ALL, 6)
        vbox.Add(self.table, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)
        pnl.SetSizer(vbox)

        # 창 크기 (가로는 표 폭에 맞추고, 세로는 스크롤 유도)
        self.SetMinSize((200, 200))
        self.SetSize((self.table.WIDTH + 50, 700))
        self.Centre()

    def onPrevPage(self, evt):
        if self.currpage <= 1:
            return
        self.currpage -= 1
        self.fr = (self.currpage - 1) * self.page_cap
        self.to = min(self.fr + self.page_cap, len(self.rows))
        self.table.display(self.currpage, self.fr, self.to, self.maxpage)
        self.lbl_page.SetLabel(u"%d / %d" % (self.currpage, self.maxpage))

    def onNextPage(self, evt):
        if self.currpage >= self.maxpage:
            return
        self.currpage += 1
        self.fr = (self.currpage - 1) * self.page_cap
        self.to = min(self.fr + self.page_cap, len(self.rows))
        self.table.display(self.currpage, self.fr, self.to, self.maxpage)
        self.lbl_page.SetLabel(u"%d / %d" % (self.currpage, self.maxpage))
