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
        self.TABLE_H = int(self.HEAD_H + max(1, nlines) * self.LINE_HEIGHT)
        self.TITLE_W = sum(self.COL_W)
        self.WIDTH   = int(BOR + self.TITLE_W + BOR)
        self.HEIGHT  = int(BOR + self.TABLE_H + BOR)
        self.SetVirtualSize((self.WIDTH, self.HEIGHT))
        self.SetScrollRate(commonwnd.CommonWnd.SCROLL_RATE, commonwnd.CommonWnd.SCROLL_RATE)

    def compute_and_draw(self):
        self.rows = dec.build_main(self.chart, self.options, cycles=2)  # L1/L2 only
        self.row_lv = [int(r.get('level', 2)) for r in self.rows]
        self._recalc_sizes(len(self.rows))
        self.drawBkg()

    def _row_at(self, y):
        BOR = commonwnd.CommonWnd.BORDER
        top = BOR + self.HEAD_H
        if y < top or y >= top + len(self.rows) * self.LINE_HEIGHT:
            return -1
        return int((y - top) // self.LINE_HEIGHT)

    def _on_click(self, event):
        pos = event.GetPosition()
        x, y = self.CalcUnscrolledPosition(pos.x, pos.y)
        ri = self._row_at(y)
        if ri < 0 or ri >= len(self.rows):
            return
        row = self.rows[ri]
        lvl = int(row.get('level', 2))
        if lvl == 2:
            # L2 → L3+L4 합본 팝업(발렌스식)
            parent_fr = self.GetTopLevelParent() or self.GetParent()
            fr = DecPopupFrame(parent_fr, self.chart, self.options, parent_row=row, level=34,
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

        # ── 헤더 박스 ──
        head_y = BOR
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
        top = BOR + self.HEAD_H
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
            start_s = dec.fmt_date(r['start'])
            len_s   = dec.fmt_length(r)

            # 행성 색
            if self.bw:
                clrpl = (0, 0, 0)
            else:
                if getattr(self.options, 'useplanetcolors', False):
                    clrpl = self._rgb(self.options.clrindividual[p])
                else:
                    clrpl = txt

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
        fr = DecPopupFrame(self, self.chart, self.options, parent_row=row, level=4,
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
            start_s = dec.fmt_date(r['start'])
            len_s   = dec.fmt_length(r)

            # 색
            clrpl = (0,0,0) if self.bw else ( self._rgb(self.options.clrindividual[p]) if getattr(self.options,'useplanetcolors',False) else txt )

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
    def __init__(self, parent, chrt, opts, parent_row, level, title=u"Decennials"):
        wx.Frame.__init__(self, parent, -1, title, wx.DefaultPosition, wx.Size(DecPopupFrame.XSIZE, DecPopupFrame.YSIZE))
        self.w = _DecPopupWnd(self, chrt, opts, parent, parent_row, level)
        self.SetMinSize((200, 200))
        self.Bind(wx.EVT_CLOSE, lambda e: e.Skip())
