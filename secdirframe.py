# -*- coding: utf-8 -*-

import transitframe
import common
import mtexts
import wx
import astrology
import chart
import wx.grid as gridlib
import sweastrology as swe
import planets as pl
import util
import math
# ---------- CommonWnd 표용 유틸 ----------
import Image, ImageDraw, ImageFont
import commonwnd
# --- replace this whole function (near the top) ---
def _load_planet_glyphs(options):
    # Morinus 빌드에 따라 Planets, Planets1/2 이름이 다를 수 있음
    for attr in ('Planets1', 'Planets2', 'Planets'):
        glyphs = getattr(common.common, attr, None)
        if isinstance(glyphs, (list, tuple)) and len(glyphs) >= 10:
            return glyphs
    # 폴백(유니코드) — 순서: Sun..Pluto (PID_TO_PIDX와 매칭)
    return (u'☉', u'☽', u'☿', u'♀', u'♂', u'♃', u'♄', u'♅', u'♆', u'♇')


def _load_fonts(options, size):
    f_text = ImageFont.truetype(common.common.abc,     size)   # 일반 텍스트
    f_sym  = ImageFont.truetype(common.common.symbols, size)   # 사인/행성/ASC·MC 기호
    return f_text, f_sym

def _load_sign_glyphs(options):
    # antiscia/positions 패턴: Signs1 / (옵션 off 시) Signs2
    signs = common.common.Signs1
    try:
        if hasattr(options, 'signs') and not options.signs:
            signs = common.common.Signs2
    except:
        pass
    return signs  # 12개 문자열(모리누스 심볼 TTF로 그릴 것)

def _deg360_to_sign_dms(lon_deg):
    """360° → (sign idx, deg, min, sec) with rollover handling."""
    x = float(lon_deg) % 360.0
    sign = int(x // 30)
    d = x - 30.0 * sign
    dd, dm, ds = util.decToDeg(d)
    if ds == 60:
        ds = 0; dm += 1
    if dm == 60:
        dm = 0; dd += 1
    if dd == 30:
        dd = 0; sign = (sign + 1) % 12
    return sign, dd, dm, ds



# PySwisseph에 obl_ecl가 없을 수도 있으므로, 진짜(또는 근사) 황도경사각을 반환
def _eps_deg(jd_ut):
    try:
        # 일부 배포에서만 존재
        return swe.obl_ecl(jd_ut)[0]
    except Exception:
        pass
    # Laskar (IAU) 근사식: J2000 기준 세기수 T
    T = (jd_ut - 2451545.0) / 36525.0
    return (23.0 + 26.0/60.0 + 21.448/3600.0) \
           - (46.8150/3600.0)*T \
           - (0.00059/3600.0)*(T**2) \
           + (0.001813/3600.0)*(T**3)

# ---- Helpers for declination ----
def _obl_deg(jd_ut):
    return swe.obl_ecl(jd_ut)[0]

def _decl_from_ecl(lon_deg, lat_deg, jd_ut):
    eps = _obl_deg(jd_ut)
    ra_deg, dec_deg, _ = swe.cotrans((lon_deg, lat_deg, 1.0), eps)
    return dec_deg

def _fmt_deg(x):
    sign = u'+' if x >= 0 else u'-'
    ax = abs(x)
    d = int(ax)
    m = int((ax - d) * 60)
    s = int(round(((ax - d) * 60 - m) * 60))
    if s == 60:
        s = 0; m += 1
    if m == 60:
        m = 0; d += 1
    return u"%02d°%02d'%02d\"" % (d, m, s), sign

def _fmt_lon(x):
    # normalize 0..360
    x = x % 360.0
    deg, mi, se = util.decToDeg(x)
    return u"%03d°%02d'%02d\"" % (deg, mi, se)

def _fmt_lat(x):
    txt, sign = _fmt_deg(x)
    return (u'+' if sign=='+' else u'-') + txt  # include sign explicitly

def _dodecatemoria(lon_deg):
    # 12th-part: sign*30 + (lon%30)*12, wrap 360
    sign_index = int(lon_deg // 30)
    intra = lon_deg - sign_index*30.0
    dode = (sign_index*30.0 + intra*12.0) % 360.0
    return _fmt_lon(dode)

def _decl_txt(lon_deg, lat_deg, jd_ut):
    dec = _decl_from_ecl(lon_deg, lat_deg, jd_ut)
    txt, sign = _fmt_deg(dec)
    return (u'+' if dec >= 0 else u'-') + txt

NAIBOD_YEAR_DAYS = 365.2422


class SecDirFrame(transitframe.TransitFrame):

    def _calflag_from_chart(self):
        return astrology.SE_JUL_CAL if self.chart.time.cal == chart.Time.JULIAN else astrology.SE_GREG_CAL

    def _update_age_and_realdate(self):

        birth_jd = self.radix.time.jd
        prog_jd  = self.chart.time.jd
        age_years_int = int(round(prog_jd - birth_jd))  

   
        real_jd = birth_jd + age_years_int * NAIBOD_YEAR_DAYS
        calflag = self._calflag_from_chart()
        y, m, d, _ = astrology.swe_revjul(real_jd, calflag)

   
        try:
            if not self.GetStatusBar():
                self.CreateStatusBar(2)
                sb = self.GetStatusBar()
                app = wx.GetApp()
                top = app.GetTopWindow() if app else None
                main_sb = top.GetStatusBar() if top else None
                if sb and main_sb:
                    sb.SetFont(main_sb.GetFont())
                    self.SendSizeEvent()

                self.SetStatusWidths([-1, -1])
            self.SetStatusText("%s: %d" % (mtexts.txts['Age'], age_years_int), 0)
            self.SetStatusText("%s: %04d.%02d.%02d" % (mtexts.txts['Real'], y, m, d), 1)
        except Exception:
            pass


        base = self.GetTitle()
        tag = " | %s: %d | %s: %04d.%02d.%02d" % (mtexts.txts['Age'], age_years_int, mtexts.txts['Real'], y, m, d)
        marker = " | " + mtexts.txts['Age'] + ":"
        if marker in base:
            base = base.split(marker)[0]

        self.SetTitle(base + tag)

    def __init__(self, parent, title, chrt, radix, options):
        transitframe.TransitFrame.__init__(self, parent, title, chrt, radix, options)
        self._update_age_and_realdate()


    def change(self, chrt, title):
        self.chart = chrt
        self.w.chart = chrt
        self.w.drawBkg()
        self.w.Refresh()

        #Update Caption
        title = title.replace(mtexts.txts['Radix'], mtexts.txts['SecondaryDir']+' ('+str(self.chart.time.year)+'.'+common.common.months[self.chart.time.month-1]+'.'+str(self.chart.time.day)+' '+str(self.chart.time.hour)+':'+str(self.chart.time.minute).zfill(2)+':'+str(self.chart.time.second).zfill(2)+')')
        self.SetTitle(title)
        self._update_age_and_realdate()
class SecProgPosWnd(commonwnd.CommonWnd):
    """
    Positions for date — CommonWnd + PIL 표.
    Columns: Body | Ecliptic | Latitude | Dodecatemorion | Declination
    - Ecliptic: 360° 값을 "dd°mm' <사인기호>"로 변환하여 중앙정렬(숫자=f_text, 기호=f_sym로 분리 렌더)
    - 나머지 칸은 텍스트 폰트로 중앙정렬
    """
    COLS = (mtexts.txts["Planets"], mtexts.txts["Longitude"], mtexts.txts["Latitude"], mtexts.txts["Dodecatemorion"], mtexts.txts["Declination"])

    ROWS = [
        ("Saturn",      astrology.SE_SATURN),
        ("Jupiter",     astrology.SE_JUPITER),
        ("Mars",        astrology.SE_MARS),
        ("Sun",         astrology.SE_SUN),
        ("Venus",       astrology.SE_VENUS),
        ("Mercury",     astrology.SE_MERCURY),
        ("Moon",        astrology.SE_MOON),
        ("Uranus",      astrology.SE_URANUS),
        ("Neptune",     astrology.SE_NEPTUNE),
        ("Pluto",       astrology.SE_PLUTO),
        ("NorthNode",  getattr(astrology, "SE_TRUE_NODE", astrology.SE_MEAN_NODE)),
    ]

    def __init__(self, parent, prg_chart, options, mainfr, id=-1, size=wx.DefaultSize):
        commonwnd.CommonWnd.__init__(self, parent, prg_chart, options, id, size)
        self.mainfr  = mainfr
        self.chart   = prg_chart
        self.options = options
        self.bw      = options.bw

        # 폰트/치수 (fixed stars 톤)
        self.FONT_SIZE   = int(21 * self.options.tablesize)
        self.SPACE       = self.FONT_SIZE / 2
        self.LINE_HEIGHT = self.SPACE + self.FONT_SIZE + self.SPACE
        self.HEAD_H      = self.LINE_HEIGHT

        self.f_text, self.f_sym = _load_fonts(self.options, self.FONT_SIZE)
        self.signs = _load_sign_glyphs(self.options)
        self.pglyphs = _load_planet_glyphs(self.options)

        # 모리누스 폰트의 북교점 글리프는 Planets 배열의 노드 인덱스에 들어있음
        node_idx = getattr(astrology, 'SE_MEAN_NODE', getattr(astrology, 'SE_TRUE_NODE', None))
        self.nnode = (self.pglyphs[node_idx]
                    if (self.pglyphs and node_idx is not None) else getattr(common.common, 'NNode', u'?'))

        # 남교점은 빌드마다 상수명이 다를 수 있으므로 안전 탐색
        self.snode = (getattr(common.common, 'SNode', None)
                    or getattr(common.common, 'SouthNode', None)
                    or getattr(common.common, 'Snode', None)
                    or u'☋')   # 최후 폴백(□로 보일 수 있음)

        # 칼럼 폭
        self.W_BODY = int(5 * self.FONT_SIZE)  # 행성/교점 1글자 + 좌우 여백 정도
        even = int(8.4 * self.FONT_SIZE)         # 나머지 칼럼 기본 폭(동일)
        self.COL_W = (self.W_BODY, even, even, even, even)
        self.TITLE_W = sum(self.COL_W)

        # 데이터 뽑기
        self._build_rows()

        # 크기/스크롤
        BOR = commonwnd.CommonWnd.BORDER
        self.TABLE_H = int(self.HEAD_H + max(1, len(self.rows)) * self.LINE_HEIGHT)
        self.WIDTH   = int(BOR + self.TITLE_W + BOR)
        self.HEIGHT  = int(BOR + self.TABLE_H + BOR)
        self.SetVirtualSize((self.WIDTH, self.HEIGHT))

        self.drawBkg()

    def getExt(self):  # 저장 확장자
        return u"SecondaryPosition.bmp"
    def _build_rows(self):
        """self.rows 구성: (Body, (ecl_num,ecl_sign), lat_txt, (dode_num,dode_sign), dec_txt)"""
        self.rows = []
        jd_ut = self.chart.time.jd
        PID_TO_PIDX = {
            astrology.SE_SUN:0, astrology.SE_MOON:1, astrology.SE_MERCURY:2,
            astrology.SE_VENUS:3, astrology.SE_MARS:4, astrology.SE_JUPITER:5,
            astrology.SE_SATURN:6, astrology.SE_URANUS:7, astrology.SE_NEPTUNE:8,
            astrology.SE_PLUTO:9,
        }
        node_id = getattr(astrology, "SE_TRUE_NODE", astrology.SE_MEAN_NODE)

        for name, pid in self.ROWS:
            if pid is None:
                # South Node
                dat = self.chart.planets.planets[node_id].data
                lon = (dat[pl.Planet.LONG] + 180.0) % 360.0
                lat = -dat[pl.Planet.LAT]
                body = self.snode
            else:
                dat = self.chart.planets.planets[pid].data
                lon = dat[pl.Planet.LONG]
                lat = dat[pl.Planet.LAT]
                if pid == node_id:
                    body = self.nnode
                else:
                    body = self.pglyphs[PID_TO_PIDX[pid]]
            # …(아래는 그대로)

            # Ecliptic: 숫자(DMS) + 사인 기호 분리
            si, d, m, s = _deg360_to_sign_dms(lon)
            ecl_num  = u"%02d°%02d'%02d\"" % (d, m, s)
            ecl_sign = self.signs[si]

            # Latitude(+/−dd°mm'ss")
            sign = u'+' if lat >= 0 else u'-'
            ld, lm, ls = util.decToDeg(abs(lat))
            lat_txt = u"%s%02d°%02d'%02d\"" % (sign, ld, lm, ls)

            # Dodecatemorion → sign + DMS
            x = lon % 360.0
            sign_idx = int(x // 30); intra = x - sign_idx * 30.0
            dode = (sign_idx * 30.0 + intra * 12.0) % 360.0
            si2, d2, m2, s2 = _deg360_to_sign_dms(dode)
            dode_num  = u"%02d°%02d'%02d\"" % (d2, m2, s2)
            dode_sign = self.signs[si2]

            # Declination (ecliptic→equatorial)
            eps = _eps_deg(jd_ut)
            try:
                _, dec_deg, _ = swe.cotrans((lon, lat, 1.0), eps)
            except Exception:
                er  = math.radians(eps)
                lam = math.radians(lon); bet = math.radians(lat)
                sin_dec = math.sin(bet)*math.cos(er) + math.cos(bet)*math.sin(er)*math.sin(lam)
                dec_deg = math.degrees(math.asin(max(-1.0, min(1.0, sin_dec))))
            sgn = u'+' if dec_deg >= 0 else u'-'
            ddg, dmm, dss = util.decToDeg(abs(dec_deg))
            dec_txt = u"%s%02d°%02d'%02d\"" % (sgn, ddg, dmm, dss)

            self.rows.append((body, (ecl_num, ecl_sign), lat_txt, (dode_num, dode_sign), dec_txt))

    def drawBkg(self):
        BOR = commonwnd.CommonWnd.BORDER
        bkg = (255,255,255) if self.bw else self.options.clrbackground
        tbl = (0,0,0)       if self.bw else self.options.clrtable
        txt = (0,0,0)       if self.bw else self.options.clrtexts
        self.SetBackgroundColour(bkg)

        img  = Image.new('RGB', (self.WIDTH, self.HEIGHT), bkg)
        draw = ImageDraw.Draw(img)

        # [헤더] (헤더 안 세로줄 없음 스타일을 원하면 outline 없이 채우기만)
        head_y = BOR
        draw.rectangle(((BOR, head_y), (BOR + self.TITLE_W, head_y + self.HEAD_H)), fill=bkg)
        x = BOR
        COLS = (mtexts.txts["Planets"], mtexts.txts["Longitude"], mtexts.txts["Latitude"], mtexts.txts["Dodecatemorion"], mtexts.txts["Declination"])
        for i, h in enumerate(COLS):
            tw, th = draw.textsize(h, self.f_text)
            draw.text((x + (self.COL_W[i]-tw)/2, head_y + (self.HEAD_H-th)/2), h, fill=txt, font=self.f_text)
            x += self.COL_W[i]
        x0 = BOR; y0 = head_y + self.HEAD_H
        draw.line((x0, y0, x0 + self.TITLE_W, y0), fill=tbl)
        # [세로선] 헤더 아래부터 본문 끝까지
        top = y0; bot = BOR + self.TABLE_H
        xv = x0
        draw.line((xv, top, xv, bot), fill=tbl)
        for w in self.COL_W:
            xv += w; draw.line((xv, top, xv, bot), fill=tbl)

        # [본문]
        y = y0
        for body, (ecl_num, ecl_sign), lat_txt, (dode_num, dode_sign), dec_txt in self.rows:
            # 가로 하단선
            draw.line((x0, y + self.LINE_HEIGHT, x0 + self.TITLE_W, y + self.LINE_HEIGHT), fill=tbl)

            xx = x0

            # Body (행성/노드 기호 = 심볼 폰트)
            tw, th = draw.textsize(body, self.f_sym)
            pclr = txt
            if not self.bw:
                idx = None
                try:
                    idx = self.pglyphs.index(body)   # Sun..Pluto/Node 인덱스
                except Exception:
                    idx = None
                if idx is not None:
                    if getattr(self.options, 'useplanetcolors', False) and hasattr(self.options, 'clrindividual'):
                        try:
                            pclr = self.options.clrindividual[idx]
                        except Exception:
                            pclr = txt
                    else:
                        try:
                            dign = int(self.chart.dignity(idx))
                        except Exception:
                            dign = 0
                        pal = [self.options.clrdomicil, self.options.clrexal,
                            self.options.clrperegrin, self.options.clrcasus, self.options.clrexil]
                        i = dign if 0 <= dign < len(pal) else 0
                        pclr = pal[i]
            draw.text((xx + (self.COL_W[0]-tw)/2, y + (self.LINE_HEIGHT-th)/2), body, fill=pclr, font=self.f_sym)

            xx += self.COL_W[0]

            # Ecliptic (숫자=f_text + 사인=f_sym 합산 중앙)
            tw, th = draw.textsize(ecl_num, self.f_text)
            gw, gh = draw.textsize(ecl_sign, self.f_sym)
            total  = tw + int(self.FONT_SIZE*0.35) + gw  # 숫자와 기호 사이 간격 약간
            base_x = xx + (self.COL_W[1] - total)/2
            cy     = y + (self.LINE_HEIGHT - th)/2
            draw.text((base_x, cy), ecl_num, fill=pclr, font=self.f_text)
            draw.text((base_x + tw + int(self.FONT_SIZE*0.35),
                       y + (self.LINE_HEIGHT - gh)/2), ecl_sign, fill=pclr, font=self.f_sym)
            xx += self.COL_W[1]

            # Latitude
            tw, th = draw.textsize(lat_txt, self.f_text)
            draw.text((xx + (self.COL_W[2]-tw)/2, y + (self.LINE_HEIGHT-th)/2), lat_txt, fill=pclr, font=self.f_text)
            xx += self.COL_W[2]

            # Dodecatemorion (숫자=f_text + 사인=f_sym 합산 중앙)
            tw, th = draw.textsize(dode_num, self.f_text)
            gw, gh = draw.textsize(dode_sign, self.f_sym)
            total  = tw + int(self.FONT_SIZE*0.35) + gw
            base_x = xx + (self.COL_W[3] - total)/2
            draw.text((base_x, y + (self.LINE_HEIGHT-th)/2), dode_num, fill=pclr, font=self.f_text)
            draw.text((base_x + tw + int(self.FONT_SIZE*0.35),
                    y + (self.LINE_HEIGHT-gh)/2), dode_sign, fill=pclr, font=self.f_sym)
            xx += self.COL_W[3]

            # Declination
            tw, th = draw.textsize(dec_txt, self.f_text)
            draw.text((xx + (self.COL_W[4]-tw)/2, y + (self.LINE_HEIGHT-th)/2), dec_txt, fill=pclr, font=self.f_text)

            y += self.LINE_HEIGHT

        # [외곽]
        draw.rectangle(((BOR,BOR),(BOR + self.TITLE_W, BOR + self.TABLE_H)), outline=tbl)

        # wx 비트맵으로 보내기
        wxImg = wx.Image(self.WIDTH, self.HEIGHT); wxImg.SetData(img.tobytes())
        self.buffer = wx.Bitmap(wxImg)
        self.Refresh()

    # 데이터 갱신용(필요 시 호출)
    def refresh_data(self, prg_chart):
        self.chart = prg_chart
        self._build_rows()
        self.drawBkg()

class SecProgPosFrame(wx.Frame):
    
    """
    Positions for date — CommonWnd 표 프레임.
    - fpathimgs 필드를 둬서 CommonWnd 저장(onSaveAsBitmap) 호환
    """
    def __init__(self, parent, title, prg_chart, options=None, buddy_dlg=None):
        wx.Frame.__init__(
            self, parent, -1, title, size=(760, 480),
            style=wx.DEFAULT_FRAME_STYLE | wx.FRAME_FLOAT_ON_PARENT
        )

        # ← 추가: 호출부가 options를 안 줄 때를 대비해 가져오기
        opts = options
        if opts is None:
            opts = getattr(parent, 'options', None)
        if opts is None:
            opts = getattr(prg_chart, 'options', None)
        if opts is None:
            raise TypeError("options missing: pass options or ensure parent.options exists")

        self.horoscope = prg_chart
        self.options   = opts
        self.fpathimgs = u""

        self.panel = SecProgPosWnd(self, prg_chart, opts, mainfr=self)  # ← opts로 교체
        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(s)
        self._buddy_dlg = buddy_dlg
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self.SetMinSize((200, 200))
        self.SetSize((650, 450))
        self.CentreOnScreen()
        self.peer_dialog = None
        self.Bind(wx.EVT_CLOSE, self._on_close)  # ← 표 X 누르면 다이얼로그도 닫기
        self.Show()
        pos = self.GetPosition()
        self.SetPosition((pos[0] +330, pos[1]+40));
    # 외부에서 차트 바뀔 때 호출
    def change_chart(self, prg_chart):
        self.horoscope = prg_chart
        self.panel.refresh_data(prg_chart)
    def link_dialog(self, dlg):
        """표 프레임과 날짜 다이얼로그를 연결한다."""
        self.peer_dialog = dlg
        # Reparent 금지: wx.Dialog 같은 최상위 창은 Reparent 하면 사라질 수 있음.

    def _on_close(self, evt):
        # 표(X) 닫힘 → 연결된 날짜 팝업도 함께 닫기 (두 방식 모두 지원)
        for attr in ("_buddy_dlg", "peer_dialog"):
            dlg = getattr(self, attr, None)
            if dlg:
                try:
                    if hasattr(dlg, "IsModal") and dlg.IsModal():
                        dlg.EndModal(wx.ID_CLOSE)
                    else:
                        dlg.Destroy()
                except Exception:
                    try:
                        dlg.Destroy()
                    except Exception:
                        pass
                setattr(self, attr, None)
        # 표 프레임 종료
        self.Destroy()

# backward-compat alias (module level, NOT inside class)
SecProgPosTableFrame = SecProgPosFrame