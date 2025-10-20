# -*- coding: utf-8 -*-
import wx, os, math, datetime
from PIL import Image, ImageDraw, ImageFont
import common, commonwnd as cw, mtexts, astrology, util
import fixstardirs
import primdirs
import mtexts
import chart
import intvalidator
import rangechecker

# ---------- 테이블(프라이머리 디렉션 스타일, CommonWnd 상속) ----------
class FixStarDirsWnd(cw.CommonWnd):
    SCROLL_RATE = 20
    BORDER = 20

    SEC1 = 0
    SEC5 = 1
    SEC10 = 2
    MIN1 = 3
    MIN5 = 4
    MIN10 = 5

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

        self.WIDTH  = int(FixStarDirsWnd.BORDER + self.TITLE_CELL_WIDTH + FixStarDirsWnd.BORDER)
        self.TABLE_HEIGHT = (self.TITLE_CELL_HEIGHT + self.SPACE_TITLEY + self.LINE_NUM * self.LINE_HEIGHT)
        self.HEIGHT = int(FixStarDirsWnd.BORDER + self.TABLE_HEIGHT + FixStarDirsWnd.BORDER)
        self.SetVirtualSize((self.WIDTH, self.HEIGHT))

        # 폰트
        self.fntMorinus = ImageFont.truetype(common.common.symbols, int(self.FONT_SIZE))
        self.fntSymbol  = ImageFont.truetype(common.common.symbols, int(3 * self.FONT_SIZE / 2))   # D/C 화살표용 '-'
        self.fntAspects = ImageFont.truetype(common.common.symbols, int(3 * self.FONT_SIZE / 4))   # 각 기호
        self.fntText    = ImageFont.truetype(common.common.abc,     int(self.FONT_SIZE))

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
                #return u"Dynamic Key: True Solar (Equatorial)"
                return mtexts.txts["DynamicKey"]+": " + mtexts.txts['TrueSolarEquatorialArc']
            if d == primdirs.PrimDirs.TRUESOLARECLIPTICALARC:
                #return u"Dynamic Key: True Solar (Ecliptical)"
                return mtexts.txts["DynamicKey"]+": " + mtexts.txts["TrueSolarEclipticalArc"]
            if d == primdirs.PrimDirs.BIRTHDAYSOLAREQUATORIALARC:
                #return u"Dynamic Key: Birthday Solar (Equatorial)"
                return mtexts.txts["DynamicKey"]+": " + mtexts.txts["BirthdaySolarEquatorialArc"]
            if d == primdirs.PrimDirs.BIRTHDAYSOLARECLIPTICALARC:
                #return u"Dynamic Key: Birthday Solar (Ecliptical)"
                return mtexts.txts["DynamicKey"]+": " + mtexts.txts["BirthdaySolarEclipticalArc"]
            return mtexts.txts["DynamicKey"]
        # 정적 키
        s = getattr(opt, 'pdkeys', None)
        if s == primdirs.PrimDirs.NAIBOD:
            return mtexts.txts["StaticKey"]+": "+mtexts.txts["Naibod"]
        if s == primdirs.PrimDirs.CARDAN:
            return mtexts.txts["StaticKey"]+": "+mtexts.txts["Cardan"]
        if s == primdirs.PrimDirs.PTOLEMY:
            return mtexts.txts["StaticKey"]+": "+mtexts.txts["Ptolemy"]
        if s == primdirs.PrimDirs.CUSTOMER:
            # 사용자 지정 값 표시(도/분/초)
            deg = getattr(opt, 'pdkeydeg', 0)
            minu = getattr(opt, 'pdkeymin', 0)
            sec = getattr(opt, 'pdkeysec', 0)
            return (mtexts.txts["StaticKey"]+": "+mtexts.txts["Custom"]+ "(%d° %d′ %d″)") % (deg, minu, sec)
        # 안전망(기본)
        return  mtexts.txts["StaticKey"]+":"+mtexts.txts["Naibod"]

    # 그리기
    def drawBkg(self):
        img  = Image.new('RGB', (max(self.WIDTH,1), max(self.HEIGHT,1)), self.bkgclr)
        draw = ImageDraw.Draw(img)

        BOR = FixStarDirsWnd.BORDER

        # Title 박스
        draw.rectangle(((BOR, BOR), (BOR + self.TITLE_CELL_WIDTH, BOR + self.TITLE_CELL_HEIGHT)),
                       outline=self.tableclr, fill=self.bkgclr)
        keytxt = self._pd_key_title()
        title  = mtexts.txts["MundaneOnly"] + keytxt
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
        headers = (mtexts.txts["Age"], mtexts.txts["Prom"], u"D/C", mtexts.txts["Sig"], mtexts.txts["Arc"], mtexts.txts["Date"])
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
        wximg = wx.Image(img.size[0], img.size[1])
        wximg.SetData(img.tobytes())
        self.buffer = wx.Bitmap(wximg)

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
        #prom = unicode(r.get('prom', u""))
        prom = str(r.get('prom', u""))
        self._center_text(draw, x, y, 1, prom, self.fntText, tclr)

        # 3) D/C (+ 화살표: 심볼 폰트 '-')
        #d_is_direct = unicode(r.get('dc', u"D")).upper().startswith(u"D")
        d_is_direct = str(r.get('dc', u"D")).upper().startswith(u"D")
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

        # 4) Sig. (ASC/DSC → 지역화 표기)
        sig_raw = str(r.get('sig', u""))
        sig_norm = sig_raw.replace(u'ASC', u'Asc').replace(u'DSC', u'Dsc')  # 내부 정규화
        _tr = {'Asc': mtexts.txts['Asc'], 'Dsc': mtexts.txts['Dsc'],
            'MC': mtexts.txts['MC'],   'IC':  mtexts.txts['IC']}
        # 예: "Asc/MC" 같은 패턴도 대비
        for k, v in _tr.items():
            sig_norm = sig_norm.replace(k, v)
        self._center_text(draw, x, y, 3, sig_norm, self.fntText, tclr)


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
        wx.Frame.__init__(self, parent, title=mtexts.txts['FixStarAngleDirs'])
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

        # ---- PD와 동일한 툴바(아이콘 순서: 위/뒤/앞/아래) ----
        self.tb = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)
        tsize = (24, 24)
        bmp_up      = wx.ArtProvider.GetBitmap(wx.ART_GO_UP,      wx.ART_TOOLBAR, tsize)
        bmp_back    = wx.ArtProvider.GetBitmap(wx.ART_GO_BACK,    wx.ART_TOOLBAR, tsize)
        bmp_forward = wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_TOOLBAR, tsize)
        bmp_down    = wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN,    wx.ART_TOOLBAR, tsize)

        self.tb.SetToolBitmapSize(tsize)

        # PD와 같은 ID/순서: Start(UP=첫 페이지) → Back(이전 페이지) → Forward(다음 페이지) → End(DOWN=마지막 페이지)
        self.ID_Start   = 10
        self.ID_Back    = 20
        self.ID_Forward = 30
        self.ID_End     = 40

        self.tb.AddTool(self.ID_Start,   "Start",   bmp_up,      shortHelp=mtexts.txts.get("Start","Start"))
        self.tb.AddTool(self.ID_Back,    "Back",    bmp_back,    shortHelp=mtexts.txts.get("Back","Back"))
        self.tb.AddTool(self.ID_Forward, "Forward", bmp_forward, shortHelp=mtexts.txts.get("Forward","Forward"))
        self.tb.AddTool(self.ID_End,     "End",     bmp_down,    shortHelp=mtexts.txts.get("End","End"))

        self.Bind(wx.EVT_TOOL, self.OnStart,   id=self.ID_Start)
        self.Bind(wx.EVT_TOOL, self.OnBack,    id=self.ID_Back)
        self.Bind(wx.EVT_TOOL, self.OnForward, id=self.ID_Forward)
        self.Bind(wx.EVT_TOOL, self.OnEnd,     id=self.ID_End)
        self.tb.AddSeparator()
        # ---- 시간/생시보정 바: PD와 동일한 순서/간격으로 "툴바 왼쪽 정렬" ----
        # 간격 유틸(툴바 컨트롤 사이 픽셀 폭 고정)
        def _tb_spacer(w):
            st = wx.StaticText(self.tb, -1, u'')
            st.SetMinSize((w, -1))   # 폭 고정
            self.tb.AddControl(st)

        # 연도 범위 (PD와 동일 로직)
        rnge = 3000
        try:
            checker = rangechecker.RangeChecker()
            if checker.isExtended():
                rnge = 5000
        except Exception:
            pass

        t = self.horoscope.time

        # [아이콘 그룹]과 필드 사이 여백
        self.tb.AddControl(wx.StaticText(self.tb, -1, '              '))

        # YYYY
        self.year = wx.TextCtrl(self.tb, -1, '', validator=intvalidator.IntValidator(0, rnge),
                                size=(50,-1), style=wx.TE_READONLY)
        self.year.SetMaxLength(4)
        self.year.SetValue(str(getattr(t, 'origyear', getattr(t, 'year', 0))))
        self.tb.AddControl(self.year)
        self.tb.AddControl(wx.StaticText(self.tb, -1, ' '))

        # MM
        self.month = wx.TextCtrl(self.tb, -1, '', validator=intvalidator.IntValidator(1, 12),
                                size=(30,-1), style=wx.TE_READONLY)
        self.month.SetMaxLength(2)
        self.month.SetValue(str(getattr(t, 'origmonth', getattr(t, 'month', 1))).zfill(2))
        self.tb.AddControl(self.month)
        self.tb.AddControl(wx.StaticText(self.tb, -1, ' '))

        # DD
        self.day = wx.TextCtrl(self.tb, -1, '', validator=intvalidator.IntValidator(1, 31),
                            size=(30,-1), style=wx.TE_READONLY)
        self.day.SetMaxLength(2)
        self.day.SetValue(str(getattr(t, 'origday', getattr(t, 'day', 1))).zfill(2))
        self.tb.AddControl(self.day)

        # 날짜와 시간 사이 여백 (PD 간격)
        self.tb.AddControl(wx.StaticText(self.tb, -1, '   '))

        # hh:mm:ss  (PD처럼 ':'로 구분)
        self.hour = wx.TextCtrl(self.tb, -1, '', validator=intvalidator.IntValidator(0, 23),
                                size=(30,-1), style=wx.TE_READONLY)
        self.hour.SetMaxLength(2)
        self.hour.SetValue(str(getattr(t, 'hour', 0)))
        self.tb.AddControl(self.hour)

        self.tb.AddControl(wx.StaticText(self.tb, -1, ':'))

        self.minute = wx.TextCtrl(self.tb, -1, '', validator=intvalidator.IntValidator(0, 59),
                                size=(30,-1), style=wx.TE_READONLY)
        self.minute.SetMaxLength(2)
        self.minute.SetValue(str(getattr(t, 'minute', 0)).zfill(2))
        self.tb.AddControl(self.minute)

        self.tb.AddControl(wx.StaticText(self.tb, -1, ':'))

        self.sec = wx.TextCtrl(self.tb, -1, '', validator=intvalidator.IntValidator(0, 59),
                            size=(30,-1), style=wx.TE_READONLY)
        self.sec.SetMaxLength(2)
        self.sec.SetValue(str(getattr(t, 'second', 0)).zfill(2))
        self.tb.AddControl(self.sec)

        # 시간과 '생시보정' 사이 여백 (PD 간격)
        self.tb.AddControl(wx.StaticText(self.tb, -1, '     '))

        # '생시보정' 라벨(다국어) + ':' (라벨만 mtexts에서 꺼냄 → 다국어)
        self.tb.AddControl(wx.StaticText(self.tb, -1, mtexts.txts['Rectification']))
        self.tb.AddControl(wx.StaticText(self.tb, -1, ': '))

        # Rectification 콤보 (PD와 동일 choices)
        self.recttypes = ('1s', '5s', '10s', '1m', '5m', '10m')
        self.rectcb = wx.ComboBox(self.tb, -1, self.recttypes[0], size=(70,-1),
                                choices=self.recttypes, style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.rectcb.SetSelection(0)
        self.tb.AddControl(self.rectcb)

        # 콤보와 +/- 사이 여백
        self.tb.AddControl(wx.StaticText(self.tb, -1, ' '))

        # + / - (보정 증감)
        self.btnIncr = wx.Button(self.tb, -1, '+', size=(40,30))
        self.tb.AddControl(self.btnIncr)
        self.btnDecr = wx.Button(self.tb, -1, '-', size=(40,30))
        self.tb.AddControl(self.btnDecr)

        # 계산 버튼 전 여백
        self.tb.AddControl(wx.StaticText(self.tb, -1, '  '))

        # Calculate (다국어)
        self.btnCalc = wx.Button(self.tb, -1, mtexts.txts.get('Calculate', u'Calculate'), size=(-1,30))
        self.tb.AddControl(self.btnCalc)

        # 버튼 이벤트 (PD와 동일)
        self.Bind(wx.EVT_BUTTON, self.onIncr, id=self.btnIncr.GetId())
        self.Bind(wx.EVT_BUTTON, self.onDecr, id=self.btnDecr.GetId())
        self.Bind(wx.EVT_BUTTON, self.onCalc, id=self.btnCalc.GetId())

        self.tb.Realize()

        # ---- 테이블 ----
        self.table = FixStarDirsWnd(pnl, self.horoscope, self.options, mainfr=self)
        self.table.set_data(self.rows, self.currpage, self.maxpage, self.fr, self.to)

        vbox.Add(self.table, 1, wx.EXPAND, 0)
        pnl.SetSizer(vbox)

        # ↑/↓용 임시 메뉴 ID
        try:
            up_id = wx.NewIdRef()
            down_id = wx.NewIdRef()
        except AttributeError:
            up_id = wx.NewId()
            down_id = wx.NewId()
        self._ID_SCROLL_UP = int(up_id)
        self._ID_SCROLL_DOWN = int(down_id)

        # ↑/↓ 키가 들어오면 표 스크롤로 처리
        self.Bind(wx.EVT_MENU, self.onScrollUp,   id=self._ID_SCROLL_UP)
        self.Bind(wx.EVT_MENU, self.onScrollDown, id=self._ID_SCROLL_DOWN)

        accels = [
            (wx.ACCEL_NORMAL, wx.WXK_LEFT,  self.ID_Back),
            (wx.ACCEL_NORMAL, wx.WXK_RIGHT, self.ID_Forward),
            (wx.ACCEL_NORMAL, wx.WXK_UP,    self._ID_SCROLL_UP),      # ↑ : 스크롤 위
            (wx.ACCEL_NORMAL, wx.WXK_DOWN,  self._ID_SCROLL_DOWN),    # ↓ : 스크롤 아래
            # (선택) Home/End를 첫/마지막 페이지로 매핑하고 싶으면 아래 두 줄 추가
            # (wx.ACCEL_NORMAL, wx.WXK_HOME, self.btn_first.GetId()),
            # (wx.ACCEL_NORMAL, wx.WXK_END,  self.btn_last.GetId()),
        ]
        self.SetAcceleratorTable(wx.AcceleratorTable(accels))

        # 포커스가 표로 가 있도록 해주면 ↑/↓ 스크롤 체감이 자연스러움
        self.table.SetFocus()
        # 초기 버튼 상태 반영 (PD와 동일)
        self._update_tb_enabled()

        # 창 크기 (가로는 표 폭에 맞추고, 세로는 스크롤 유도)
        self.SetMinSize((200, 200))
        self.SetSize((self.table.WIDTH + 50, 700))
        self.Centre()
        
    def onScrollUp(self, evt=None):
        try:
            x, y = self.table.GetViewStart()
            # 스크롤 단위(ScrollRate)에 맞춰 한 칸 위로
            self.table.Scroll(x, max(0, y - 1))
        except Exception:
            pass

    def onScrollDown(self, evt=None):
        try:
            x, y = self.table.GetViewStart()
            self.table.Scroll(x, y + 1)
        except Exception:
            pass

    def onPrevPage(self, evt=None):
        if self.currpage <= 1:
            return
        self.currpage -= 1
        self.fr = (self.currpage - 1) * self.page_cap
        self.to = min(self.fr + self.page_cap, len(self.rows))
        self.table.display(self.currpage, self.fr, self.to, self.maxpage)
        self._update_tb_enabled()

    def onNextPage(self, evt=None):
        if self.currpage >= self.maxpage:
            return
        self.currpage += 1
        self.fr = (self.currpage - 1) * self.page_cap
        self.to = min(self.fr + self.page_cap, len(self.rows))
        self.table.display(self.currpage, self.fr, self.to, self.maxpage)
        self._update_tb_enabled()

    def _update_tb_enabled(self):
        # PD와 동일 UX: 경계에서 비활성화
        self.tb.EnableTool(self.ID_Start,   self.currpage != 1)
        self.tb.EnableTool(self.ID_Back,    self.currpage != 1)
        self.tb.EnableTool(self.ID_Forward, self.currpage != self.maxpage)
        self.tb.EnableTool(self.ID_End,     self.currpage != self.maxpage)

    def OnStart(self, evt=None):
        if self.currpage != 1:
            self.currpage = 1
            self.fr = 0
            self.to = min(self.page_cap, len(self.rows))
            self.table.display(self.currpage, self.fr, self.to, self.maxpage)
            self._update_tb_enabled()

    def OnBack(self, evt=None):
        self.onPrevPage()

    def OnForward(self, evt=None):
        self.onNextPage()

    def OnEnd(self, evt=None):
        if self.currpage != self.maxpage:
            self.currpage = self.maxpage
            self.fr = (self.currpage - 1) * self.page_cap
            self.to = min(self.fr + self.page_cap, len(self.rows))
            self.table.display(self.currpage, self.fr, self.to, self.maxpage)
            self._update_tb_enabled()

    def _update_nav_enabled(self):
        at_first = (self.currpage <= 1)
        at_last  = (self.currpage >= self.maxpage)

    def _goto_page(self, page):
        if self.maxpage <= 0:
            return
        page = max(1, min(int(page), int(self.maxpage)))
        self.currpage = page
        self.fr = (self.currpage - 1) * self.page_cap
        self.to = min(self.fr + self.page_cap, len(self.rows))
        self.table.display(self.currpage, self.fr, self.to, self.maxpage)
        self._update_nav_enabled()

    def _get_fields(self):
        return (int(self.year.GetValue()),
                int(self.month.GetValue()),
                int(self.day.GetValue()),
                int(self.hour.GetValue()),
                int(self.minute.GetValue()),
                int(self.sec.GetValue()))

    def _set_fields(self, y, m, d, h, mi, s):
        self.year.SetValue(str(y))
        self.month.SetValue(str(m).zfill(2))
        self.day.SetValue(str(d).zfill(2))
        self.hour.SetValue(str(h))
        self.minute.SetValue(str(mi).zfill(2))
        self.sec.SetValue(str(s).zfill(2))

    def _adjust_time(self, seconds):
        y, m, d, h, mi, s = self._get_fields()
        try:
            base = datetime.datetime(y, m, d, h, mi, s)
            base = base + datetime.timedelta(seconds=seconds)
            self._set_fields(base.year, base.month, base.day, base.hour, base.minute, base.second)
        except Exception:
            pass

    def onIncr(self, evt=None):
        idx = self.rectcb.GetCurrentSelection()
        step = (1, 5, 10, 60, 300, 600)[idx if 0 <= idx < 6 else 0]
        self._adjust_time(step)

    def onDecr(self, evt=None):
        idx = self.rectcb.GetCurrentSelection()
        step = (1, 5, 10, 60, 300, 600)[idx if 0 <= idx < 6 else 0]
        self._adjust_time(-step)

    def onCalc(self, evt=None):
        # 필드 → Time/Chart 재생성 → 데이터 재계산 → 1페이지부터 표시
        y, m, d, h, mi, s = self._get_fields()
        ot = self.horoscope.time
        new_time = chart.Time(y, m, d, h, mi, s,
                            ot.bc, ot.cal, ot.zt, ot.plus, ot.zh, ot.zm,
                            ot.daylightsaving, self.horoscope.place)
        self.horoscope = chart.Chart(self.horoscope.name, self.horoscope.male,
                                    new_time, self.horoscope.place, self.horoscope.htype,
                                    self.horoscope.notes, self.horoscope.options)

        self.rows = fixstardirs.compute_fixedstar_angle_rows(self.horoscope, self.options, age_max_years=150.0)
        self.currpage = 1
        self.fr = 0
        self.to = min(self.page_cap, len(self.rows))
        self.maxpage = max(1, int(math.ceil(len(self.rows) / float(self.page_cap))))
        self.table.set_data(self.rows, self.currpage, self.maxpage, self.fr, self.to)
        self.table.display(self.currpage, self.fr, self.to, self.maxpage)
        self._update_tb_enabled()
