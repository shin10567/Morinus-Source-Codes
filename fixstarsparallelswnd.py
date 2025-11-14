# -*- coding: utf-8 -*-
import math
import wx
import os
import astrology
import planets
import fixstars
import fixstardirs
import fortune
import houses
import chart
import common
import commonwnd
import Image, ImageDraw, ImageFont
import mtexts
import util

ARCSEC = 3600.0

def _absdeg(x): return abs(x)
def _degdiff(a, b): return abs(a - b)

class FixStarsParallelsWnd(commonwnd.CommonWnd):
    """
    Tables > Fixed Stars > Fixed Star Parallels
    Declination Parallels between angles/planets/points and selected fixed stars.
    """

    def __init__(self, parent, chrt, options, mainfr, id=-1, size=wx.DefaultSize):
        commonwnd.CommonWnd.__init__(self, parent, chrt, options, id, size)
        self.mainfr = mainfr

        # === sizes: follow positionswnd ===
        self.FONT_SIZE = int(21 * self.options.tablesize)
        self.SPACE = self.FONT_SIZE // 2
        self.LINE_HEIGHT = self.SPACE + self.FONT_SIZE + self.SPACE

        self.SMALL_CELL_WIDTH = 3 * self.FONT_SIZE         # symbol/point
        self.CELL_WIDTH = 8 * self.FONT_SIZE               # decl columns
        self.BIG_CELL_WIDTH = 10 * self.FONT_SIZE          # star name (as fixstarswnd)

        self.COLUMN_NUM = 4  # (blank/point) | decl_pt | star_name | decl_star

        BOR = commonwnd.CommonWnd.BORDER
        self.TABLE_WIDTH = self.SMALL_CELL_WIDTH + self.CELL_WIDTH + self.BIG_CELL_WIDTH + self.CELL_WIDTH
        header_h = self.LINE_HEIGHT
        body_rows = self._row_count()
        self.TABLE_HEIGHT = header_h + body_rows * self.LINE_HEIGHT

        self.WIDTH  = int(2 * BOR + self.TABLE_WIDTH)
        self.HEIGHT = int(2 * BOR + self.TABLE_HEIGHT)

        self.SetBackgroundColour(self.options.clrbackground)
        self.SetVirtualSize((self.WIDTH, self.HEIGHT))


        # fonts: follow positionswnd/fixstarswnd
        self.fntMorinus = ImageFont.truetype(common.common.symbols, int(self.FONT_SIZE))
        self.fntSymbol  = ImageFont.truetype(common.common.symbols, int(3 * self.FONT_SIZE / 2))
        self.fntText    = ImageFont.truetype(common.common.abc, int(self.FONT_SIZE))
        self.fntTextBold = ImageFont.truetype(common.common.abc_bold, int(self.FONT_SIZE)) if os.path.exists(common.common.abc_bold) else self.fntText
        self.deg_symbol = u'\u00b0'

        # dignity 팔레트 (positionswnd와 동일)
        self.clrs = (self.options.clrdomicil, self.options.clrexal,
                    self.options.clrperegrin, self.options.clrcasus, self.options.clrexil)

        # glyphs (angles) same codes as fixstarsaspectswnd
        self.GLY_ANGLE = {'ASC': u'0', 'MC': u'1', 'IC': u'2', 'DSC': u'3'}
        # Node glyphs: use the same shared symbols as other windows
        # Node glyphs: use shared symbols; fallback to unicode then draw with text font
        self.NN_CHAR = getattr(common.common, 'nnode', None)
        self.SN_CHAR = getattr(common.common, 'snode', None)
        # 보조 시도: Planets 맵의 확장 인덱스 사용(환경에 따라 존재)
        if not self.NN_CHAR:
            try:
                self.NN_CHAR = common.common.Planets[astrology.SE_PLUTO+1]
            except Exception:
                pass
        if not self.SN_CHAR:
            try:
                self.SN_CHAR = common.common.Planets[astrology.SE_PLUTO+2]
            except Exception:
                pass
        # 최종 폴백: 유니코드
        if not self.NN_CHAR: self.NN_CHAR = u'☊'
        if not self.SN_CHAR: self.SN_CHAR = u'☋'
        # 유니코드 폴백이면 심볼 폰트 대신 텍스트 폰트 사용
        self._node_use_text_font = (self.NN_CHAR in (u'☊',) or self.SN_CHAR in (u'☋',))

        self.LOF_CHAR = u'4'

        # color setup
        self.tableclr = (0,0,0) if self.bw else self.options.clrtable
        self.textclr  = (0,0,0) if self.bw else self.options.clrtexts

        # precompute star magnitudes map by code (lazy on demand)
        self._mag_cache = {}

        # precompute decls of points
        self._points = self._collect_points()

        self.buffer = None
        self.drawBkg()

    # ---- CommonWnd hook for Save As Bitmap file name suffix ----
    def getExt(self):
        # 파일명 꼬리표(예: John_Doe_FixStarParallels.bmp). mtexts 키 없이도 안전하게 동작
        return u'_FixStarParallels'

    # ---------- geometry helpers ----------
    def _row_count(self):
        # header + each point as one row with possibly multiple star matches -> we draw point once then matched stars stacked
        # For height estimate we conservatively allocate one line per point; drawing handles multi-matches by stacking extra lines.
        # To avoid dynamic resize flicker, keep this simple: allocate Npoints * max(1, avg matches). We'll stick to 1; wx scroll handles overflow.
        return len(self._point_order())

    def _point_order(self):
        # Angles first, then planets, nodes, fortuna
        return ['ASC','DSC','MC','IC',
                astrology.SE_SUN, astrology.SE_MOON, astrology.SE_MERCURY, astrology.SE_VENUS,
                astrology.SE_MARS, astrology.SE_JUPITER, astrology.SE_SATURN,
                astrology.SE_URANUS, astrology.SE_NEPTUNE, astrology.SE_PLUTO,
                'NN', 'SN', 'LOF']

    # ---------- data collection ----------
    def _collect_points(self):
        pts = {}
        obl = self.chart.obl[0]

        # Angles decl from ascmc2 (ASC/MC), others compute
        asc_lon  = self.chart.houses.ascmc2[houses.Houses.ASC][houses.Houses.LON]
        asc_decl = self.chart.houses.ascmc2[houses.Houses.ASC][houses.Houses.DECL]
        mc_lon   = self.chart.houses.ascmc2[houses.Houses.MC][houses.Houses.LON]
        mc_decl  = self.chart.houses.ascmc2[houses.Houses.MC][houses.Houses.DECL]
        # Dsc/IC decl from ecliptic lon+180, lat=0
        dsc_ra, dsc_decl, _ = astrology.swe_cotrans(util.normalize(asc_lon + 180.0), 0.0, 1.0, -obl)
        ic_ra,  ic_decl,  _ = astrology.swe_cotrans(util.normalize(mc_lon  + 180.0),  0.0, 1.0, -obl)

        pts['ASC'] = asc_decl
        pts['DSC'] = dsc_decl
        pts['MC']  = mc_decl
        pts['IC']  = ic_decl

        # Planets decl (Swiss Ephem already computed in chart.planets)
        for p in (astrology.SE_SUN, astrology.SE_MOON, astrology.SE_MERCURY, astrology.SE_VENUS,
                  astrology.SE_MARS, astrology.SE_JUPITER, astrology.SE_SATURN,
                  astrology.SE_URANUS, astrology.SE_NEPTUNE, astrology.SE_PLUTO):
            pts[p] = self.chart.planets.planets[p].dataEqu[planets.Planet.DECLEQU]

        # Nodes: mean/true node in chart as SE node; SN opposite
        node_decl = self.chart.planets.planets[astrology.SE_PLUTO+1].dataEqu[planets.Planet.DECLEQU]  # node appended after pluto
        # South Node is exact opposite in ecliptic longitude but decl is ~(-) of NN for small lat → 여기선 관례적으로 부호 반전 사용
        pts['NN'] = node_decl
        pts['SN'] = -node_decl

        # Fortuna decl
        # 옵션의 Lot-of-Fortune 타입을 morinus 내부 상수로 변환
        lot_idx = getattr(self.options, 'lotoffortune', 2)
        if   lot_idx == 0: lftype = chart.Chart.LFMOONSUN
        elif lot_idx == 1: lftype = chart.Chart.LFDSUNMOON
        else:              lftype = chart.Chart.LFDMOONSUN

        # 태양 고도(ELV)로 주간/야간 판정 → abovehorizon
        sun_elv = self.chart.planets.planets[astrology.SE_SUN].speculums[1][planets.Planet.ELV]
        aboveh  = (sun_elv > 0.0)

        # 황도 경사 값 안전 취득
        obl_val = self.chart.obl[0] if isinstance(self.chart.obl, (list, tuple)) else self.chart.obl

        # Fortune(typ, ascmc2, raequasc, pls, obl, placelat, abovehorizon)
        fort = fortune.Fortune(
            lftype,
            self.chart.houses.ascmc2,
            self.chart.raequasc,
            self.chart.planets,
            obl_val,
            self.chart.place.lat,
            aboveh
        )

        pts['LOF'] = fort.fortune[fortune.Fortune.DECL]

        return pts

    # ---------- magnitude & bold threshold ----------
    def _star_mag(self, code, fallback_name=None):
        key = code or (fallback_name or '')
        if key in self._mag_cache:
            return self._mag_cache[key]
        mag = None
        try:
            _ra, _dc, mag, _frame = fixstardirs._cat_lookup_equ_generic(code or fallback_name or '')
        except Exception:
            pass
        self._mag_cache[key] = mag
        return mag

    def _bold_orb_deg(self, mag):
        # minutes → degrees
        if mag is None:
            return 5.0/60.0  # 보수적(가장 엄격)
        if mag < 0.0:
            return 10.0/60.0
        if 0.0 <= mag < 1.0:
            return 8.0/60.0
        if 1.0 <= mag <= 1.5:
            return 6.0/60.0
        return 5.0/60.0
    def drawBkg(self):
        # CommonWnd가 호출하는 재그리기 엔트리. 흑백 토글 후에도 여기로 들어옴.
        self.Draw()

    # ---------- drawing ----------
    def Draw(self):
        BOR = commonwnd.CommonWnd.BORDER
        img = Image.new('RGB', (int(self.WIDTH), int(self.HEIGHT)), (255,255,255) if self.bw else self.options.clrbackground)
        draw = ImageDraw.Draw(img)

        # header (no left title)
        x = BOR; y = BOR
        self._draw_header(draw, x, y)
        y += self.LINE_HEIGHT

        # rows
        for key in self._point_order():
            y = self._draw_point_row(draw, x, y, key)

        wxImg = wx.Image(img.size[0], img.size[1])
        wxImg.SetData(img.tobytes())
        self.buffer = wx.Bitmap(wxImg)
        self.Refresh(False)

    def _draw_header(self, draw, x, y):
        # top border intentionally omitted (positionswnd style)
        txtclr = (0,0,0) if self.bw else self.options.clrtexts

        offs = (0, self.SMALL_CELL_WIDTH, self.CELL_WIDTH, self.BIG_CELL_WIDTH, self.CELL_WIDTH)

        # 헤더 세로선:
        # - 왼쪽 Declination의 '왼쪽' 경계선만 유지
        draw.line((x + self.SMALL_CELL_WIDTH, y, x + self.SMALL_CELL_WIDTH, y + self.LINE_HEIGHT), fill=self.tableclr)
        # - Fixed Star 양쪽 세로 구분선은 그리지 않음
        # - 오른쪽 Declination의 '오른쪽'(표의 맨 오른쪽) 테두리 추가
        draw.line((x + self.TABLE_WIDTH, y, x + self.TABLE_WIDTH, y + self.LINE_HEIGHT), fill=self.tableclr)

        # 헤더 하단선: 표 전체 폭 유지
        draw.line((x, y + self.LINE_HEIGHT, x + self.TABLE_WIDTH, y + self.LINE_HEIGHT), fill=self.tableclr)

        # 헤더 상단선: Asc 칸은 제외 → 왼쪽 Declination 시작점부터 오른쪽 테두리까지
        draw.line((x + self.SMALL_CELL_WIDTH, y, x + self.TABLE_WIDTH, y), fill=self.tableclr)

        # captions
        # captions (localized)
        cap_decl = mtexts.txts['Declination']  # exists in all langs
        cap_star = mtexts.txts.get('FixedStar', mtexts.txts.get('FixedStar','Fixed Star'))  # fallback to plural or EN
        captions = ('', cap_decl, cap_star, cap_decl)

        # locale: keep English minimal; advanced localization unnecessary here
        for idx, cap in enumerate(captions):
            if not cap:
                continue
            colx = x + sum(offs[:idx+1])
            w,h = draw.textsize(cap, self.fntText)
            draw.text((colx + (offs[idx+1]-w)/2, y + (self.LINE_HEIGHT-h)/2), cap, fill=txtclr, font=self.fntText)

    def _draw_point_row(self, draw, x, y, point_key):
        # cell grid bottom line
        draw.line((x, y+self.LINE_HEIGHT, x+self.TABLE_WIDTH, y+self.LINE_HEIGHT), fill=self.tableclr)

        offs = (0, self.SMALL_CELL_WIDTH, self.CELL_WIDTH, self.BIG_CELL_WIDTH, self.CELL_WIDTH)
        for i in range(1, len(offs)-1):
            draw.line((x+sum(offs[:i+1]), y, x+sum(offs[:i+1]), y+self.LINE_HEIGHT), fill=self.tableclr)
        # left/right outer borders for the row
        draw.line((x, y, x, y+self.LINE_HEIGHT), fill=self.tableclr)
        draw.line((x+self.TABLE_WIDTH, y, x+self.TABLE_WIDTH, y+self.LINE_HEIGHT), fill=self.tableclr)

        txtclr = (0,0,0) if self.bw else self.options.clrtexts

        # 1) left cell: symbol/name (행성/각/노드/LoF는 심볼폰트 1.5×, N/S는 텍스트)
        sym = self._point_symbol(point_key)
        if (isinstance(point_key, int) and astrology.SE_SUN <= point_key <= astrology.SE_PLUTO) \
        or point_key in ('ASC','DSC','MC','IC','NN','SN','LOF'):
            fontL = self.fntSymbol
        else:
            fontL = self.fntText

        iconclr = self._label_color(point_key)
        w, h = draw.textsize(sym, fontL)
        draw.text((x + (self.SMALL_CELL_WIDTH - w)//2, y + (self.LINE_HEIGHT - h)//2),
                sym, fill=iconclr, font=fontL)
        # 2) point decl (first decl column) + 행 볼드 결정
        pdecl = self._points.get(point_key, None)
        matches = self._compute_matches(pdecl)

        row_bold = False
        for _code, _name, sdecl, _mag in matches:
            if pdecl is not None and sdecl is not None and (pdecl * sdecl) >= 0.0:
                if _degdiff(pdecl, sdecl) <= self._bold_orb_deg(_mag):
                    row_bold = True
                    break

        txt_decl_pt = self._fmt_decl(pdecl)
        font_decl_pt = self.fntTextBold if row_bold else self.fntText
        w,h = draw.textsize(txt_decl_pt, font_decl_pt)
        draw.text((x + offs[1] + (self.CELL_WIDTH - w)/2, y + (self.LINE_HEIGHT - h)/2),
                  txt_decl_pt, fill=txtclr, font=font_decl_pt)

        # 3) fixed stars matches (within 15′ and same sign)
        #    If multiple matches, we print first on this line, push subsequent ones as extra lines underneath.

        if matches:
            first, rest = matches[0], matches[1:]
            self._draw_star_cols(draw, x, y, first, pdecl, row_bold)
            # stack others
            y0 = y
            for m in rest:
                y0 += self.LINE_HEIGHT
                # bottom border for stacked line
                draw.line((x, y0+self.LINE_HEIGHT, x+self.TABLE_WIDTH, y0+self.LINE_HEIGHT), fill=self.tableclr)
                for i in range(1, len(offs)-1):
                    draw.line((x+sum(offs[:i+1]), y0, x+sum(offs[:i+1]), y0+self.LINE_HEIGHT), fill=self.tableclr)
                # empty left + point decl reused visually as ditto mark(“)
                self._draw_star_cols(draw, x, y0, m, pdecl, row_bold)
                # left/right outer borders for the stacked line
                draw.line((x, y0, x, y0+self.LINE_HEIGHT), fill=self.tableclr)
                draw.line((x+self.TABLE_WIDTH, y0, x+self.TABLE_WIDTH, y0+self.LINE_HEIGHT), fill=self.tableclr)

            return y0 + self.LINE_HEIGHT
        else:
            # 매치가 하나도 없으면 두 칸 모두 '—' 출력
            dash = u'—'
            # Fixed Star 칸
            colx = x + sum(offs[:3])
            w,h = draw.textsize(dash, self.fntText)
            draw.text((colx + (offs[3]-w)/2, y + (self.LINE_HEIGHT - h)/2), dash, fill=txtclr, font=self.fntText)
            # 오른쪽 Declination 칸
            w,h = draw.textsize(dash, self.fntText)
            draw.text((x + sum(offs[:4]) + (self.CELL_WIDTH - w)/2, y + (self.LINE_HEIGHT - h)/2),
                      dash, fill=txtclr, font=self.fntText)
            return y + self.LINE_HEIGHT

    def _draw_star_cols(self, draw, x, y, match, pdecl, row_bold):
        txtclr = (0,0,0) if self.bw else self.options.clrtexts
        code, dispname, sdecl, mag = match

        # 행 전체 볼드: 조건 충족 시 이름/적위 모두 Bold (행성 기호는 이미 별도로 비볼드)
        font_nm   = self.fntTextBold if row_bold else self.fntText
        font_decl = font_nm

        offs = (0, self.SMALL_CELL_WIDTH, self.CELL_WIDTH, self.BIG_CELL_WIDTH, self.CELL_WIDTH)
        # 이름
        colx = x + sum(offs[:3])
        w,h  = draw.textsize(dispname, font_nm)
        draw.text((colx + (offs[3]-w)/2, y + (self.LINE_HEIGHT-h)/2), dispname, fill=txtclr, font=font_nm)
        # 항성 적위
        txt_decl_star = self._fmt_decl(sdecl)
        w,h  = draw.textsize(txt_decl_star, font_decl)
        draw.text((x + sum(offs[:4]) + (self.CELL_WIDTH-w)/2, y + (self.LINE_HEIGHT-h)/2),
                  txt_decl_star, fill=txtclr, font=font_decl)


    # ---------- computations ----------
    def _compute_matches(self, pdecl):
        res = []
        if pdecl is None:
            return res
        for idx in range(len(self.chart.fixstars.data)):
            code = self.chart.fixstars.data[idx][fixstars.FixStars.NOMNAME]
            name_sw = self.chart.fixstars.data[idx][fixstars.FixStars.NAME] or code
            disp = astrology.display_fixstar_name(code, self.options, name_sw)
            sdecl = self.chart.fixstars.data[idx][fixstars.FixStars.DECL]
            # sign equal & within 15'
            if pdecl * sdecl < 0:
                continue
            if _degdiff(pdecl, sdecl) <= (15.0/60.0):
                mag = self._star_mag(code, name_sw)
                res.append((code, disp, sdecl, mag))
        # keep sorted by absolute orb
        res.sort(key=lambda x: _degdiff(pdecl, x[2]))
        return res

    # ---------- presentation helpers ----------
    def _fmt_decl(self, val):
        if val is None:
            return u'—'
        d, m, s = util.decToDeg(abs(val) + 1e-8)
        sign = '-' if val < 0.0 else ''
        # positionswnd 규칙: 부호는 음수만 '-', 도·분·초 모두 표시, 공백 없음, 분/초 기호 ' / "
        return sign + (str(int(d))).rjust(2) + u'\u00b0' + (str(int(m))).zfill(2) + "'" + (str(int(s))).zfill(2) + '"'


    def _label_color(self, key):
        # BW면 무조건 검정
        if self.bw:
            return (0, 0, 0)

        # 행성: 개인색 사용 or 존위색(dignity)
        if isinstance(key, int) and astrology.SE_SUN <= key <= astrology.SE_PLUTO:
            if self.options.useplanetcolors:
                return self.options.clrindividual[key]
            dign = self.chart.dignity(key)
            return self.clrs[dign]

        # 노드(N/S) 개인색
        if key in ('NN', 'SN'):
            return self.options.clrindividual[astrology.SE_PLUTO+1] if self.options.useplanetcolors else self.options.clrtexts

        # 포르투나(LoF) 개인색
        if key == 'LOF':
            return self.options.clrindividual[astrology.SE_PLUTO+2] if self.options.useplanetcolors else self.options.clrtexts

        # 각도(ASC/DSC/MC/IC)나 기타 기본
        return self.options.clrtexts

    def _is_symbol(self, s):
        try:
            return isinstance(s, str) and len(s) == 1
        except Exception:
            return False


    def _point_symbol(self, key):
        # angles
        if key == 'ASC': return self.GLY_ANGLE['ASC']
        if key == 'DSC': return self.GLY_ANGLE['DSC']
        if key == 'MC' : return self.GLY_ANGLE['MC']
        if key == 'IC' : return self.GLY_ANGLE['IC']
        # Fortuna glyph (as positionswnd)
        # Fortuna
        if key == 'LOF':
            return self.LOF_CHAR
        # Nodes (from fixstarsaspectswnd or fallback set in __init__)
        if key == 'NN':
            return self.NN_CHAR
        if key == 'SN':
            return self.SN_CHAR
        # Planets: use the configured symbol map (user setting respected; incl. Uranus/Pluto)
        if isinstance(key, int) and astrology.SE_SUN <= key <= astrology.SE_PLUTO:
            try:
                return common.common.Planets[key]
            except Exception:
                # 안전 폴백(환경 독립)
                fallback = {
                    astrology.SE_SUN: u'A',  astrology.SE_MOON: u'B',   astrology.SE_MERCURY: u'C',
                    astrology.SE_VENUS: u'D',astrology.SE_MARS: u'E',   astrology.SE_JUPITER: u'F',
                    astrology.SE_SATURN: u'G',astrology.SE_URANUS: u'H',astrology.SE_NEPTUNE: u'I',
                    astrology.SE_PLUTO: u'J',
                }
                return fallback.get(key, u'?')
        return u'?'

