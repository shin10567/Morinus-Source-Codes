# -*- coding: utf-8 -*-
import wx, datetime
from PIL import Image, ImageDraw, ImageFont
import common, commonwnd
import astrology
import mtexts
import decennials as dec

class DecWnd(commonwnd.CommonWnd):
    def __init__(self, parent, horoscope, options, mainfr, id=-1, size=wx.DefaultSize):
        commonwnd.CommonWnd.__init__(self, parent, horoscope, options, id, size)
        self.mainfr = mainfr
        self.bw = self.options.bw

        # ZR L3/L4와 완전히 동일
        self.FONT_SIZE   = int(21 * self.options.tablesize)
        self.SPACE       = self.FONT_SIZE / 2
        self.LINE_HEIGHT = self.SPACE + self.FONT_SIZE + self.SPACE
        self.HEAD_H      = self.LINE_HEIGHT
        self.INFO_H      = self.LINE_HEIGHT  # 헤더 위 정보행(“Start TopicalPlanet: ..”)
        self.start_selector = 'sect'         # 기본: 섹트 라이트

        # 폰트 (Morinus TTF) — ZR과 동일
        self.fntText     = ImageFont.truetype(common.common.abc,       self.FONT_SIZE)
        self.fntTextBold = ImageFont.truetype(common.common.abc_bold,  self.FONT_SIZE)
        self.fntMor      = ImageFont.truetype(common.common.symbols,   self.FONT_SIZE)

        # 컬럼폭 — ZR 값 그대로
        self.W_LEVEL = int(2.8 * self.FONT_SIZE)
        self.W_PLAN  = int(3.0 * self.FONT_SIZE)   # (ZR의 Sign 폭)
        self.W_START = int(7.0 * self.FONT_SIZE)
        self.W_LEN   = int(7.0 * self.FONT_SIZE)
        self.COL_W   = (self.W_LEVEL, self.W_PLAN, self.W_START, self.W_LEN)
        self.TITLE_W = sum(self.COL_W)

        self.rows = []
        self.row_lv = []
        self.compute_and_draw()
        # 마우스 클릭으로 L3/L4 팝업 열기(ZR과 동일 UX)
        self.Bind(wx.EVT_LEFT_UP, self._on_click)
        self._child_frames = []  # 자식 프레임 레퍼런스 유지

    def set_start_selector(self, selector):
        self.start_selector = (selector or 'sect')

    def _rgb(self, col):
        # wx.Colour -> (R,G,B) 또는 이미 튜플이면 그대로
        try:
            return (col.Red(), col.Green(), col.Blue())
        except Exception:
            if isinstance(col, (tuple, list)) and len(col) >= 3:
                return (int(col[0]), int(col[1]), int(col[2]))
            return (0, 0, 0)

    def _pil_to_bitmap(self, im):
        im = im.convert('RGB')
        w, h = im.size
        wx_img = wx.Image(w, h)
        wx_img.SetData(im.tobytes())   # RGB 그대로 주입
        return wx.Bitmap(wx_img)
    def _strip_year_zeros_ymd(self, s):
        try:
            txt = s.decode('utf-8','ignore') if isinstance(s, bytes) else u"%s" % s
            suffix = u""
            if u" BC" in txt:
                core, rest = txt.split(u" BC", 1)
                suffix = u" BC" + rest
            else:
                core = txt
            parts = core.split(u".", 1)
            if len(parts) >= 2:
                y = parts[0]
                y = u"%d" % int(y)   # ← 앞 0 제거(0이면 '0')
                return y + u"." + parts[1] + suffix
            return txt
        except:
            return s

    def getExt(self):
        return u"Decennials.bmp"

    def _chart_dt(self):
        try:
            return self.chart.time.getDatetime()
        except:
            t = self.chart.time
            return datetime.datetime(int(t.year), int(t.month), int(t.day),
                                     int(t.hour), int(t.minute), int(getattr(t,'second',0)))

    def _recalc_sizes(self, nlines):
        BOR = commonwnd.CommonWnd.BORDER
        # self.HEAD_H는 __init__에서 결정됨 (ZR 동일)
        self.TABLE_H = int(self.INFO_H + self.HEAD_H + max(1, nlines) * self.LINE_HEIGHT)
        self.TITLE_W = sum(self.COL_W)
        self.WIDTH   = int(BOR + self.TITLE_W + BOR)
        self.HEIGHT  = int(BOR + self.TABLE_H + BOR)
        self.SetVirtualSize((self.WIDTH, self.HEIGHT))
        self.SetScrollRate(commonwnd.CommonWnd.SCROLL_RATE, commonwnd.CommonWnd.SCROLL_RATE)

    def compute_and_draw(self):
        self.rows = dec.build_main(self.chart, self.options, cycles=2, start_selector=self.start_selector)
        self.row_lv = [int(r.get('level', 2)) for r in self.rows]
        self._recalc_sizes(len(self.rows))
        self.drawBkg()

    def _row_at(self, y):
        BOR = commonwnd.CommonWnd.BORDER
        top = BOR + self.INFO_H + self.HEAD_H
        if y < top or y >= top + len(self.rows) * self.LINE_HEIGHT:
            return -1
        return int((y - top) // self.LINE_HEIGHT)
    def _l2_row_for_l1(self, l1_index, l1_row):
        """L1 행을 클릭했을 때, 같은 시작점의 첫 L2(보통 바로 다음 줄)를 찾아 반환한다.
        (ZR처럼 L1을 눌러도 L2와 동일한 팝업이 뜨게 하기 위함)
        """
        try:
            s = l1_row.get('start')
            p = int(l1_row.get('planet', -1))
        except Exception:
            s = None
            p = -1

        # 1) 일반 케이스: L1 다음 줄이 같은 시작의 L2
        try:
            if l1_index + 1 < len(self.rows):
                r = self.rows[l1_index + 1]
                if int(r.get('level', 0)) == 2:
                    if (s is None or r.get('start') == s) and int(r.get('planet', -2)) == p:
                        return r
        except Exception:
            pass

        # 2) L1 블록 안에서 시작점이 같은 L2를 탐색(다음 L1을 만나면 중단)
        for j in range(l1_index + 1, len(self.rows)):
            r = self.rows[j]
            lv = int(r.get('level', 0))
            if lv == 1:
                break
            if lv == 2:
                if s is None or r.get('start') == s:
                    return r

        # 3) 그래도 없으면, 같은 L1 블록의 첫 L2라도 반환
        for j in range(l1_index + 1, len(self.rows)):
            r = self.rows[j]
            lv = int(r.get('level', 0))
            if lv == 1:
                break
            if lv == 2:
                return r
        return None

    def _on_click(self, event):
        pos = event.GetPosition()
        x, y = self.CalcUnscrolledPosition(pos.x, pos.y)
        ri = self._row_at(y)
        if ri < 0 or ri >= len(self.rows):
            return
        row = self.rows[ri]
        lvl = int(row.get('level', 2))

        # ZR UX처럼: L1을 눌러도 해당 구간의 L2(첫 L2)와 동일한 팝업을 연다.
        if lvl == 1:
            l2row = self._l2_row_for_l1(ri, row)
            if l2row is not None:
                row = l2row
                lvl = 2

        if lvl == 2:

            # L2 → L3+L4 합본 팝업(발렌스식)
            parent_fr = self.GetTopLevelParent() or self.GetParent()
            fr = DecPopupFrame(parent_fr, self.chart, self.options, self.mainfr, parent_row=row, level=34,
                                        title=u"Decennials L3+L4")
            fr.Show(True); self._child_frames.append(fr)

    def drawBkg(self):
        BOR = commonwnd.CommonWnd.BORDER

        # 색 (ZR 규칙: BW면 흑백, 아니면 옵션색)
        bkg = (255, 255, 255) if self.bw else self._rgb(self.options.clrbackground)
        tbl = (0,   0,   0)   if self.bw else self._rgb(self.options.clrtable)
        txt = (0,   0,   0)   if self.bw else self._rgb(self.options.clrtexts)
        try:
            self.SetBackgroundColour(bkg)
        except Exception:
            pass

        img  = Image.new('RGB', (self.WIDTH, self.HEIGHT), bkg)
        draw = ImageDraw.Draw(img)

        # [A] 정보행: "Start: <기호/텍스트>" — 베이스라인 정렬
        label = u"%s:" % (mtexts.txts['Start'])

        sel = (self.start_selector or 'sect').lower()
        is_planet = sel in ('sun','moon','mercury','venus','mars','jupiter','saturn')

        # 왼쪽 라벨/오른쪽 값의 폰트 선택
        lab_f = self.fntText
        if is_planet:
            # 값이 행성 글리프면 심볼 폰트
            val_f = self.fntMor
            pmap = {
                'sun': astrology.SE_SUN, 'moon': astrology.SE_MOON,
                'mercury': astrology.SE_MERCURY, 'venus': astrology.SE_VENUS,
                'mars': astrology.SE_MARS, 'jupiter': astrology.SE_JUPITER,
                'saturn': astrology.SE_SATURN
            }
            p = pmap[sel]
            val_txt = common.common.Planets[p]
        else:
            # 값이 텍스트(섹트/Ascendant/LoF)
            val_f = self.fntText
            tmap = {
                'sect': mtexts.txts.get('SectLight', u'Sect Light'),
                'asc':  mtexts.txts['Ascendant'],
                'fortune': mtexts.txts['LotOfFortune']
            }
            val_txt = tmap.get(sel, tmap['sect'])

        # 색상(본문 규칙과 동일)
        txt_col = (0,0,0) if self.bw else self._rgb(self.options.clrtexts)
        if is_planet:
            if self.bw:
                glyph_col = (0,0,0)
            else:
                if getattr(self.options, 'useplanetcolors', False):
                    glyph_col = self._rgb(self.options.clrindividual[p])
                else:
                    # 존비 팔레트로 폴백
                    pal = (self.options.clrdomicil,
                           self.options.clrexal,
                           self.options.clrperegrin,
                           self.options.clrcasus,
                           self.options.clrexil)
                    glyph_col = self._rgb(pal[self.chart.dignity(p)])

        # 가로 배치 계산
        lw, lh = draw.textsize(label,  lab_f)
        vw, vh = draw.textsize(val_txt, val_f)
        gap    = int(self.FONT_SIZE * 0.5)
        total_w = lw + gap + vw
        base_x = BOR + (self.TITLE_W - total_w) / 2

        # ── 핵심: 공통 베이스라인 계산 ──
        # PIL ImageFont의 getmetrics()로 ascent/descents를 구해 둘 텍스트가 같은 베이스라인을 공유하도록 만든다.
        try:
            asc1, desc1 = lab_f.getmetrics()
        except Exception:
            # 안전 폴백(대략적인 비율)
            asc1, desc1 = int(0.8*self.FONT_SIZE), int(0.2*self.FONT_SIZE)
        try:
            asc2, desc2 = val_f.getmetrics()
        except Exception:
            asc2, desc2 = int(0.8*self.FONT_SIZE), int(0.2*self.FONT_SIZE)

        max_asc  = max(asc1, asc2)
        max_desc = max(desc1, desc2)
        # 정보행 높이 안에서 (top, bottom) = (baseline-max_asc, baseline+max_desc)가 정확히 중앙에 오도록
        baseline = BOR + (self.INFO_H - (max_asc + max_desc)) / 2 + max_asc

        # 각 텍스트의 실제 그리기 y(=top)는 baseline - ascent
        y_lab = baseline - asc1
        y_val = baseline - asc2

        # 그리기
        draw.text((base_x, y_lab), label, fill=txt_col, font=lab_f)
        if is_planet:
            draw.text((base_x + lw + gap, y_val), val_txt, fill=glyph_col, font=val_f)
        else:
            draw.text((base_x + lw + gap, y_val), val_txt, fill=txt_col,   font=val_f)

        # [B] 헤더
        head_y = BOR + self.INFO_H

        draw.rectangle(((BOR, head_y), (BOR + self.TITLE_W, head_y + self.HEAD_H)),
                    outline=None, fill=bkg)
        heads = (u"Lv.", mtexts.txts['TopicalPlanet'], mtexts.txts["Start"], mtexts.txts["Length"])
        x = BOR
        for i, h in enumerate(heads):
            tw, th = draw.textsize(h, self.fntText)
            draw.text((x + (self.COL_W[i] - tw) / 2, head_y + (self.HEAD_H - th) / 2),
                    h, fill=txt, font=self.fntText)
            x += self.COL_W[i]

        # 헤더 하단선
        x0 = BOR
        y0 = head_y + self.HEAD_H
        draw.line((x0, y0, x0 + self.TITLE_W, y0), fill=tbl)

        # ── 세로선 (헤더 아래부터 표 하단까지) ──
        top = head_y + self.HEAD_H

        bot = BOR + self.TABLE_H
        xv  = x0
        draw.line((xv, top, xv, bot), fill=tbl)
        for w in self.COL_W:
            xv += w
            draw.line((xv, top, xv, bot), fill=tbl)

        # ── 데이터 ──
        y = y0
        for r in self.rows:
            lvl = int(r.get('level', 2))
            p   = int(r['planet'])
            start_s = self._strip_year_zeros_ymd(dec.fmt_date(r['start']))
            len_s   = dec.fmt_length(r)

            # 행성 색
            if self.bw:
                clrpl = (0, 0, 0)
            else:
                if getattr(self.options, 'useplanetcolors', False):
                    clrpl = self._rgb(self.options.clrindividual[p])
                else:
                    pal = (self.options.clrdomicil,
                           self.options.clrexal,
                           self.options.clrperegrin,
                           self.options.clrcasus,
                           self.options.clrexil)
                    clrpl = self._rgb(pal[self.chart.dignity(p)])

            isL1  = (lvl == 1)
            fTxt  = self.fntText
            fTxtB = self.fntTextBold
            fMor  = self.fntMor
            xx    = x0

            # Lv.
            val = u"L%d" % lvl
            tw, th = draw.textsize(val, fTxtB if isL1 else fTxt)
            cx = xx + (self.W_LEVEL - tw) / 2
            cy = y  + (self.LINE_HEIGHT - th) / 2
            draw.text((cx, cy), val, fill=txt, font=(fTxtB if isL1 else fTxt))
            xx += self.W_LEVEL

            # Planet (모리누스 심볼) — L1은 가짜 볼드(두 번 찍기)
            glyph = common.common.Planets[p]
            tw, th = draw.textsize(glyph, fMor)
            cx = xx + (self.W_PLAN - tw) / 2
            cy = y  + (self.LINE_HEIGHT - th) / 2
            if isL1:
                draw.text((cx,   cy), glyph, fill=clrpl, font=fMor)
                draw.text((cx-1, cy), glyph, fill=clrpl, font=fMor)
            else:
                draw.text((cx, cy), glyph, fill=clrpl, font=fMor)
            xx += self.W_PLAN

            # Start
            val = start_s
            tw, th = draw.textsize(val, fTxtB if isL1 else fTxt)
            cx = xx + (self.W_START - tw) / 2
            cy = y  + (self.LINE_HEIGHT - th) / 2
            draw.text((cx, cy), val, fill=txt, font=(fTxtB if isL1 else fTxt))
            xx += self.W_START

            # Length
            val = len_s
            tw, th = draw.textsize(val, fTxtB if isL1 else fTxt)
            cx = xx + (self.W_LEN - tw) / 2
            cy = y  + (self.LINE_HEIGHT - th) / 2
            draw.text((cx, cy), val, fill=txt, font=(fTxtB if isL1 else fTxt))

            # 행 하단선
            draw.line((x0, y + self.LINE_HEIGHT, x0 + self.TITLE_W, y + self.LINE_HEIGHT), fill=tbl)
            y += self.LINE_HEIGHT

        # ── 외곽선 ──
        draw.rectangle(((BOR, BOR), (BOR + self.TITLE_W, BOR + self.TABLE_H)), outline=tbl)

        # wx Bitmap으로 변환
        self.buffer = self._pil_to_bitmap(img)
        self.Refresh(True)

class DecStartDlg(wx.Dialog):
    """
    데세니얼 시작 기준 선택 다이얼로그.
    표시 순서: Sect Light, Sun, Moon, Asc, LotOfFortune, Saturn, Jupiter, Mars, Venus, Mercury
    반환: 'sect' / 'sun' / 'moon' / 'asc' / 'fortune' / 'saturn' / 'jupiter' / 'mars' / 'venus' / 'mercury'
    """
    _TOKENS = ('sect','sun','moon','asc','fortune','saturn','jupiter','mars','venus','mercury')

    def __init__(self, parent):
        t = u"%s" % (mtexts.txts['Start'])
        wx.Dialog.__init__(self, parent, title=t)
        v = wx.BoxSizer(wx.VERTICAL)

        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(wx.StaticText(self, -1, u"%s:" % (mtexts.txts['Start'])),
                0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)

        labels = (
            mtexts.txts.get('SectLight', u'Sect Light'),
            mtexts.txts['Sun'], mtexts.txts['Moon'],
            mtexts.txts['Ascendant'], mtexts.txts['LotOfFortune'],
            mtexts.txts['Saturn'], mtexts.txts['Jupiter'], mtexts.txts['Mars'],
            mtexts.txts['Venus'], mtexts.txts['Mercury'],
        )
        self.cmb = wx.ComboBox(self, -1, choices=list(labels), style=wx.CB_READONLY)
        self.cmb.SetSelection(0)  # 기본: Sect Light
        row.Add(self.cmb, 0)

        v.Add(row, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        btns = wx.StdDialogButtonSizer()
        btns.AddButton(wx.Button(self, wx.ID_OK, mtexts.txts["Compute"]))
        btns.AddButton(wx.Button(self, wx.ID_CANCEL, mtexts.txts["Cancel"]))
        btns.Realize()
        v.Add(btns, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        self.SetSizerAndFit(v)

    def get_token(self):
        idx = int(self.cmb.GetSelection())
        return self._TOKENS[idx]

class DecennialsFrame(wx.Frame):
    XSIZE = 570
    YSIZE = 450
    def __init__(self, parent, title, chrt, opts):
        t = title
        try:
            t = t.replace(mtexts.typeList[chrt.htype], mtexts.menutxts['TMDecennials'].split('\\t')[0])
        except Exception:
            pass
        wx.Frame.__init__(self, parent, -1, t, wx.DefaultPosition, wx.Size(DecennialsFrame.XSIZE, DecennialsFrame.YSIZE))
        self.w = DecWnd(self, chrt, opts, parent)
        self.SetMinSize((200,200))

        def _on_close(e):
            try:
                for fr in list(self.w._child_frames):
                    try:
                        if fr: fr.Destroy()
                    except:
                        pass
                self.w._child_frames[:] = []
            except:
                pass
            self.Destroy()   # ← e.Skip() 대신 명시적으로 파괴
        self.Bind(wx.EVT_CLOSE, _on_close)


class _DecPopupWnd(commonwnd.CommonWnd):
    def __init__(self, parent, horoscope, options, mainfr, parent_row, level, id=-1, size=wx.DefaultSize):
        commonwnd.CommonWnd.__init__(self, parent, horoscope, options, id, size)
        self.mainfr = mainfr
        self.bw = self.options.bw
        self.parent_row = parent_row
        self.level = level

        # 메인 표와 동일 규격/폰트
        self.FONT_SIZE   = int(21 * self.options.tablesize)
        self.SPACE       = self.FONT_SIZE / 2
        self.LINE_HEIGHT = self.SPACE + self.FONT_SIZE + self.SPACE
        self.HEAD_H      = self.LINE_HEIGHT
        self.fntText     = ImageFont.truetype(common.common.abc,       self.FONT_SIZE)
        self.fntTextBold = ImageFont.truetype(common.common.abc_bold,  self.FONT_SIZE)
        self.fntMor      = ImageFont.truetype(common.common.symbols,   self.FONT_SIZE)
        self.W_LEVEL = int(2.8 * self.FONT_SIZE)
        self.W_PLAN  = int(3.0 * self.FONT_SIZE)
        self.W_START = int(7.0 * self.FONT_SIZE)
        self.W_LEN   = int(7.0 * self.FONT_SIZE)
        self.COL_W   = (self.W_LEVEL, self.W_PLAN, self.W_START, self.W_LEN)
        self.TITLE_W = sum(self.COL_W)
        self.buffer = wx.Bitmap(1, 1)  # OnPaint 초기에 안전하게 지나가도록 더미 버퍼

        self.rows = []
        self._child_frames = []
        self.compute_and_draw()

    def _rgb(self, col):
        try: return (col.Red(), col.Green(), col.Blue())
        except: return (col[0], col[1], col[2]) if isinstance(col,(tuple,list)) else (0,0,0)

    def _pil_to_bitmap(self, im):
        im = im.convert('RGB')
        w,h = im.size
        wx_img = wx.Image(w,h); wx_img.SetData(im.tobytes())
        return wx.Bitmap(wx_img)
    def _strip_year_zeros_ymd(self, s):
        try:
            txt = s.decode('utf-8','ignore') if isinstance(s, bytes) else u"%s" % s
            suffix = u""
            if u" BC" in txt:
                core, rest = txt.split(u" BC", 1)
                suffix = u" BC" + rest
            else:
                core = txt
            parts = core.split(u".", 1)
            if len(parts) >= 2:
                y = parts[0]
                y = u"%d" % int(y)   # ← 앞 0 제거(0이면 '0')
                return y + u"." + parts[1] + suffix
            return txt
        except:
            return s

    # Save As Bitmap 기본 파일명 접미사 (CommonWnd.onSaveAsBitmap에서 사용)
    def getExt(self):
        try:
            lvl = int(self.level)
        except Exception:
            lvl = None
        # L3/L4 팝업이면 레벨을 이름에 반영, 그 외 예외적으로 기본명 사용
        return u"Decennials_L%d.bmp" % lvl if lvl in (3, 4) else u"Decennials.bmp"

    def _recalc_sizes(self, nlines):
        BOR = commonwnd.CommonWnd.BORDER
        self.TABLE_H = int(self.HEAD_H + max(1, nlines) * self.LINE_HEIGHT)
        self.TITLE_W = sum(self.COL_W)
        self.WIDTH   = int(BOR + self.TITLE_W + BOR)
        self.HEIGHT  = int(BOR + self.TABLE_H + BOR)
        self.SetVirtualSize((self.WIDTH, self.HEIGHT))
        self.SetScrollRate(commonwnd.CommonWnd.SCROLL_RATE, commonwnd.CommonWnd.SCROLL_RATE)

    def compute_and_draw(self):
        if self.level == 34:
            # L3+L4 합본(시간 순으로 L3 다음에 그 L4들)
            self.rows = dec.build_children_combo_valens(self.chart, self.options, self.parent_row)
        else:
            # 단일 레벨(기존 동작 유지)
            self.rows = dec.build_children_valens(self.chart, self.options, self.parent_row, self.level)

        # 표 크기 재계산 + 실제 렌더링(버퍼 생성)
        self._recalc_sizes(len(self.rows))
        self.drawBkg()

    def _row_at(self, y):
        BOR = commonwnd.CommonWnd.BORDER
        top = BOR + self.HEAD_H
        if y < top or y >= top + len(self.rows) * self.LINE_HEIGHT:
            return -1
        return int((y - top) // self.LINE_HEIGHT)

    def _on_click(self, event):
        if self.level != 3: return
        pos = event.GetPosition()
        x, y = self.CalcUnscrolledPosition(pos.x, pos.y)
        ri = self._row_at(y)
        if ri < 0: return
        row = self.rows[ri]
        fr = DecPopupFrame(self, self.chart, self.options, self.mainfr, parent_row=row, level=4,
                        title=u"Decennials L4")
        fr.Show(True); self._child_frames.append(fr)

    def drawBkg(self):
        BOR = commonwnd.CommonWnd.BORDER
        bkg = (255,255,255) if self.bw else self._rgb(self.options.clrbackground)
        tbl = (0,0,0)       if self.bw else self._rgb(self.options.clrtable)
        txt = (0,0,0)       if self.bw else self._rgb(self.options.clrtexts)
        img  = Image.new('RGB', (self.WIDTH, self.HEIGHT), bkg)
        draw = ImageDraw.Draw(img)

        # 헤더
        head_y = BOR
        draw.rectangle(((BOR, head_y), (BOR + self.TITLE_W, head_y + self.HEAD_H)), fill=bkg)
        heads = (u"Lv.", mtexts.txts['TopicalPlanet'], mtexts.txts["Start"], mtexts.txts["Length"])
        x = BOR
        for i,h in enumerate(heads):
            tw, th = draw.textsize(h, self.fntText)
            draw.text((x + (self.COL_W[i]-tw)/2, head_y + (self.HEAD_H-th)/2), h, fill=txt, font=self.fntText)
            x += self.COL_W[i]

        # 헤더 하단선
        x0 = BOR; y0 = head_y + self.HEAD_H
        draw.line((x0, y0, x0 + self.TITLE_W, y0), fill=tbl)
        # 세로선
        top = y0; bot = BOR + self.TABLE_H; xv = x0
        draw.line((xv, top, xv, bot), fill=tbl)
        for w in self.COL_W:
            xv += w; draw.line((xv, top, xv, bot), fill=tbl)

        # 데이터
        y = y0
        for r in self.rows:
            lvl = int(r.get('level', self.level))
            p   = int(r['planet'])
            start_s = self._strip_year_zeros_ymd(dec.fmt_date(r['start']))
            len_s   = dec.fmt_length(r)

            # 색
            if self.bw:
                clrpl = (0, 0, 0)
            else:
                if getattr(self.options, 'useplanetcolors', False):
                    clrpl = self._rgb(self.options.clrindividual[p])
                else:
                    pal = (self.options.clrdomicil,
                           self.options.clrexal,
                           self.options.clrperegrin,
                           self.options.clrcasus,
                           self.options.clrexil)
                    clrpl = self._rgb(pal[self.chart.dignity(p)])

            isBold = (lvl == 3)  # L3만 볼드, L4는 보통체
            fTxt  = self.fntTextBold if isBold else self.fntText
            fMorB = True if isBold else False  # 심볼 가짜 볼드(두 번 찍기) 여부

            xx = x0
            # Lv
            val = u"L%d" % lvl
            tw, th = draw.textsize(val, fTxt)
            cx = xx + (self.W_LEVEL - tw)/2; cy = y + (self.LINE_HEIGHT - th)/2
            draw.text((cx, cy), val, fill=txt, font=fTxt)
            xx += self.W_LEVEL

            # Planet
            glyph = common.common.Planets[p]
            tw, th = draw.textsize(glyph, self.fntMor)
            cx = xx + (self.W_PLAN - tw)/2; cy = y + (self.LINE_HEIGHT - th)/2
            draw.text((cx, cy), glyph, fill=clrpl, font=self.fntMor)
            if fMorB:
                draw.text((cx-1, cy), glyph, fill=clrpl, font=self.fntMor)  # L3만 가짜볼드
            xx += self.W_PLAN

            # Start
            tw, th = draw.textsize(start_s, fTxt)
            cx = xx + (self.W_START - tw)/2; cy = y + (self.LINE_HEIGHT - th)/2
            draw.text((cx, cy), start_s, fill=txt, font=fTxt)
            xx += self.W_START

            # Length
            tw, th = draw.textsize(len_s, fTxt)
            cx = xx + (self.W_LEN - tw)/2; cy = y + (self.LINE_HEIGHT - th)/2
            draw.text((cx, cy), len_s, fill=txt, font=fTxt)

            # 행 하단선
            draw.line((x0, y + self.LINE_HEIGHT, x0 + self.TITLE_W, y + self.LINE_HEIGHT), fill=tbl)
            y += self.LINE_HEIGHT

        # 외곽선
        draw.rectangle(((BOR, BOR), (BOR + self.TITLE_W, BOR + self.TABLE_H)), outline=tbl)

        self.buffer = self._pil_to_bitmap(img)
        self.Refresh(True)

class DecPopupFrame(wx.Frame):
    XSIZE = 380
    YSIZE = 480
    def __init__(self, parent, chrt, opts, mainfr, parent_row, level, title=u"Decennials"):
        wx.Frame.__init__(self, parent, -1, title, wx.DefaultPosition, wx.Size(DecPopupFrame.XSIZE, DecPopupFrame.YSIZE))
        self.w = _DecPopupWnd(self, chrt, opts, mainfr, parent_row, level)

